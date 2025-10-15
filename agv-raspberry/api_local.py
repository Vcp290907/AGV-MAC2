#!/usr/bin/env python3
"""
API Local do Raspberry Pi
Fornece endpoints REST para comunicação com o sistema PC
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
import json
from config import get_esp32_port, HARDWARE_CONFIG
from datetime import datetime
import asyncio
import threading
import time

# Câmera e processamento de imagem
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)

class CameraStreamer:
    """Gerencia captura contínua e disponibiliza frames JPEG para streaming."""
    def __init__(self, width=640, height=480, target_fps=20, camera_index=0):
        self.width = int(width)
        self.height = int(height)
        self.target_fps = int(target_fps)
        self.camera_index = int(camera_index)
        self.running = False
        self._thread = None
        self._last_jpeg = None
        self._lock = threading.Lock()
        self._cv_cap = None
        self._picam2 = None

    def _init_camera(self):
        # Tenta Picamera2 primeiro
        if PICAMERA2_AVAILABLE:
            try:
                self._picam2 = Picamera2()
                cfg = self._picam2.create_preview_configuration(main={"format": 'RGB888', "size": (self.width, self.height)})
                self._picam2.configure(cfg)
                self._picam2.start()
                return True
            except Exception as e:
                logging.getLogger(__name__).warning(f"Falha Picamera2, tentando OpenCV: {e}")
                self._picam2 = None

        # Fallback para OpenCV
        if CV2_AVAILABLE:
            try:
                cap = cv2.VideoCapture(self.camera_index)
                if not cap.isOpened():
                    cap.release()
                    return False
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                self._cv_cap = cap
                return True
            except Exception:
                self._cv_cap = None
                return False
        return False

    def _grab_loop(self):
        interval = 1.0 / max(self.target_fps, 1)
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 80] if CV2_AVAILABLE else None
        while self.running:
            try:
                frame = None
                if self._picam2 is not None:
                    import numpy as np
                    frame = self._picam2.capture_array()
                elif self._cv_cap is not None:
                    ok, frm = self._cv_cap.read()
                    if ok:
                        frame = frm

                if frame is not None and CV2_AVAILABLE:
                    ok, buf = cv2.imencode('.jpg', frame, encode_params)
                    if ok:
                        with self._lock:
                            self._last_jpeg = buf.tobytes()

            except Exception as e:
                logging.getLogger(__name__).warning(f"Erro capturando frame: {e}")

            time.sleep(interval)

        # Cleanup
        try:
            if self._picam2 is not None:
                self._picam2.stop()
                self._picam2.close()
        except Exception:
            pass
        try:
            if self._cv_cap is not None:
                self._cv_cap.release()
        except Exception:
            pass

    def start(self):
        if self.running:
            return True
        if not self._init_camera():
            return False
        self.running = True
        self._thread = threading.Thread(target=self._grab_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None

    def get_jpeg(self):
        with self._lock:
            return self._last_jpeg

    def set_camera(self, index: int):
        """Troca o índice da câmera (para setups com 2 câmeras CSI)."""
        try:
            index = int(index)
        except Exception:
            return False
        if index == self.camera_index and self.running:
            return True
        # Reiniciar com novo índice
        if self.running:
            self.stop()
        self.camera_index = index
        return self.start()

class RaspberryAPI:
    """API local do Raspberry Pi"""

    def __init__(self, agv_system):
        self.agv_system = agv_system
        self.app = Flask(__name__)
        CORS(self.app)

        # Configurar rotas
        self.setup_routes()

        # Status da API
        self.api_status = {
            'running': True,
            'start_time': datetime.now().isoformat(),
            'requests_count': 0
        }

        # Streaming de câmera para preview (usa índice padrão do config se existir)
        try:
            default_cam = int(HARDWARE_CONFIG.get('camera', {}).get('device', 0))
        except Exception:
            default_cam = 0
        self._camera_streamer = CameraStreamer(camera_index=default_cam)

    def setup_routes(self):
        """Configura todas as rotas da API"""

        @self.app.route('/')
        def index():
            """Página inicial da API"""
            return jsonify({
                'message': 'AGV Raspberry Pi API',
                'version': '1.0.0',
                'status': 'running',
                'endpoints': [
                    'GET /status - Status do sistema',
                    'POST /execute - Executar comando',
                    'GET /camera - Status da câmera',
                    'GET /preview - Página HTML simples com stream',
                    'GET /video - Stream MJPEG da câmera',
                    'POST /shutdown - Desligar sistema'
                ]
            })

        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Retorna status atual do AGV"""
            try:
                self.api_status['requests_count'] += 1
                status = self.agv_system.get_status()
                status['api'] = self.api_status

                logger.info("Status solicitado")
                return jsonify({
                    'success': True,
                    'data': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Erro ao obter status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/execute', methods=['POST'])
        def execute_command():
            """Executa um comando no AGV"""
            try:
                self.api_status['requests_count'] += 1

                if not request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'Content-Type deve ser application/json'
                    }), 400

                command = request.get_json()

                if not command:
                    return jsonify({
                        'success': False,
                        'error': 'Comando vazio'
                    }), 400

                logger.info(f"Comando recebido: {command}")

                # Executar comando de forma assíncrona
                # TODO: Implementar execução assíncrona real
                result = {
                    'success': True,
                    'command': command,
                    'message': 'Comando recebido e em processamento',
                    'timestamp': datetime.now().isoformat()
                }

                return jsonify(result)

            except Exception as e:
                logger.error(f"Erro ao executar comando: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/move_forward', methods=['POST'])
        def move_forward():
            """Move o AGV para frente por 1 segundo"""
            try:
                self.api_status['requests_count'] += 1

                logger.info("Comando: Mover para frente por 1 segundo")

                # TODO: Implementar controle real do ESP32
                # Por enquanto, apenas simular
                result = self._execute_motor_command('forward', 1.0)

                return jsonify({
                    'success': result['success'],
                    'message': result['message'],
                    'command': 'move_forward',
                    'duration': 1.0,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Erro ao mover para frente: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/move_backward', methods=['POST'])
        def move_backward():
            """Move o AGV para trás por 1 segundo"""
            try:
                self.api_status['requests_count'] += 1

                logger.info("Comando: Mover para trás por 1 segundo")

                # TODO: Implementar controle real do ESP32
                result = self._execute_motor_command('backward', 1.0)

                return jsonify({
                    'success': result['success'],
                    'message': result['message'],
                    'command': 'move_backward',
                    'duration': 1.0,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Erro ao mover para trás: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/camera', methods=['GET'])
        def get_camera_status():
            """Retorna status da câmera"""
            try:
                self.api_status['requests_count'] += 1

                # TODO: Implementar status real da câmera
                camera_status = {
                    'available': bool(PICAMERA2_AVAILABLE or CV2_AVAILABLE),
                    'backend': 'picamera2' if PICAMERA2_AVAILABLE else ('opencv' if CV2_AVAILABLE else 'none'),
                    'resolution': f"{self._camera_streamer.width}x{self._camera_streamer.height}",
                    'fps': self._camera_streamer.target_fps,
                    'qr_detection': True,
                    'last_frame': datetime.now().isoformat()
                }

                return jsonify({
                    'success': True,
                    'data': camera_status
                })

            except Exception as e:
                logger.error(f"Erro ao obter status da câmera: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/preview', methods=['GET'])
        def preview_page():
            """Página HTML simples exibindo o stream em /video"""
            try:
                self.api_status['requests_count'] += 1
                html = f"""
                <!doctype html>
                <html>
                <head>
                  <meta charset='utf-8'>
                  <title>AGV Preview</title>
                  <style>
                    body {{ font-family: Arial, sans-serif; background: #111; color: #eee; margin: 0; padding: 0; }}
                    .wrap {{ display: flex; flex-direction: column; align-items: center; padding: 16px; }}
                    img {{ max-width: 96vw; max-height: 88vh; border: 2px solid #444; background: #000; }}
                    .info {{ margin: 8px; font-size: 14px; color: #bbb; }}
                  </style>
                </head>
                <body>
                  <div class='wrap'>
                    <div class='info'>Backend: {('picamera2' if PICAMERA2_AVAILABLE else ('opencv' if CV2_AVAILABLE else 'none'))} – {self._camera_streamer.width}x{self._camera_streamer.height} @ ~{self._camera_streamer.target_fps} FPS</div>
                    <img src="/video" alt="AGV Camera Preview" />
                  </div>
                </body>
                </html>
                """
                return Response(html, mimetype='text/html')
            except Exception as e:
                logger.error(f"Erro no preview: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/video', methods=['GET'])
        def video_stream():
            """Endpoint de stream MJPEG da câmera."""
            try:
                self.api_status['requests_count'] += 1

                # Permitir seleção de câmera via query (?cam=0 ou 1)
                cam_qs = request.args.get('cam')
                if cam_qs is not None:
                    if not self._camera_streamer.set_camera(cam_qs):
                        return jsonify({'success': False, 'error': 'Falha ao selecionar camera'}), 400

                if not self._camera_streamer.running:
                    started = self._camera_streamer.start()
                    if not started:
                        return jsonify({'success': False, 'error': 'Camera indisponível'}), 503

                def generate():
                    boundary = b'--frame\r\n'
                    while True:
                        frame = self._camera_streamer.get_jpeg()
                        if frame is None:
                            time.sleep(0.02)
                            continue
                        yield boundary
                        yield b'Content-Type: image/jpeg\r\n'
                        yield f'Content-Length: {len(frame)}\r\n\r\n'.encode('ascii')
                        yield frame
                        yield b'\r\n'

                return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

            except Exception as e:
                logger.error(f"Erro no stream de vídeo: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/shutdown', methods=['POST'])
        def shutdown():
            """Desliga o sistema AGV"""
            try:
                logger.warning("Comando de shutdown recebido")

                # Parar sistema
                self.agv_system.running = False

                return jsonify({
                    'success': True,
                    'message': 'Sistema AGV sendo desligado...',
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Erro no shutdown: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/logs', methods=['GET'])
        def get_logs():
            """Retorna logs recentes do sistema"""
            try:
                # TODO: Implementar leitura de logs
                logs = [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'message': 'Sistema funcionando normalmente'
                    }
                ]

                return jsonify({
                    'success': True,
                    'data': logs
                })

            except Exception as e:
                logger.error(f"Erro ao obter logs: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/config', methods=['GET', 'POST'])
        def config():
            """Gerencia configurações do sistema"""
            if request.method == 'GET':
                # Retornar configurações atuais
                config_data = {
                    'wifi_ssid': 'AGV_NETWORK',
                    'wifi_password': '********',
                    'camera_resolution': '640x480',
                    'motor_speed': 50,
                    'qr_detection_enabled': True
                }

                return jsonify({
                    'success': True,
                    'data': config_data
                })

            elif request.method == 'POST':
                # Atualizar configurações
                try:
                    new_config = request.get_json()

                    # TODO: Salvar configurações
                    logger.info(f"Configurações atualizadas: {new_config}")

                    return jsonify({
                        'success': True,
                        'message': 'Configurações atualizadas',
                        'data': new_config
                    })

                except Exception as e:
                    logger.error(f"Erro ao atualizar configurações: {e}")
                    return jsonify({
                        'success': False,
                        'error': str(e)
                    }), 500

        @self.app.route('/test', methods=['GET'])
        def test_connection():
            """Endpoint de teste de conectividade"""
            return jsonify({
                'success': True,
                'message': 'Conexão com Raspberry Pi OK',
                'timestamp': datetime.now().isoformat(),
                'system_info': {
                    'platform': 'Raspberry Pi',
                    'version': '1.0.0',
                    'uptime': 'Test mode'
                }
            })

    def _execute_motor_command(self, direction, duration):
        """Executa comando de movimento nos motores via ESP32"""
        try:
            logger.info(f"Executando movimento REAL: {direction} por {duration}s")

            # Importar controlador ESP32
            from esp32_control import ESP32Controller

            # Criar controlador com porta específica
            esp32 = ESP32Controller(port=get_esp32_port())

            # Conectar ao ESP32
            logger.info("Conectando ao ESP32...")
            if not esp32.connect():
                logger.error("Falha ao conectar com ESP32")
                return {
                    'success': False,
                    'message': 'Falha ao conectar com ESP32',
                    'direction': direction,
                    'duration': duration,
                    'error': 'ESP32 não conectado',
                    'timestamp': datetime.now().isoformat()
                }

            logger.info("ESP32 conectado, executando movimento...")

            # Executar movimento baseado na direção
            if direction == 'forward':
                result = esp32.move_forward(duration)
                logger.info(f"Movimento para frente executado: {result}")
            elif direction == 'backward':
                result = esp32.move_backward(duration)
                logger.info(f"Movimento para trás executado: {result}")
            else:
                esp32.disconnect()
                return {
                    'success': False,
                    'message': f'Direção inválida: {direction}',
                    'direction': direction,
                    'duration': duration,
                    'error': 'Direção não suportada',
                    'timestamp': datetime.now().isoformat()
                }

            # Desconectar
            esp32.disconnect()
            logger.info("ESP32 desconectado")

            # Retornar resultado
            result['timestamp'] = datetime.now().isoformat()
            logger.info(f"Movimento ESP32 REAL concluído: {result['message']}")
            return result

        except Exception as e:
            logger.error(f"Erro ao executar movimento REAL {direction}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f'Erro ao executar movimento: {str(e)}',
                'direction': direction,
                'duration': duration,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def run_api_server(api_instance):
    """Executa o servidor Flask em uma thread separada"""
    try:
        logger.info("Iniciando servidor API na porta 8080...")
        api_instance.app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Erro no servidor API: {e}")

async def start_api_server(agv_system):
    """Inicia o servidor API de forma assíncrona"""
    api = RaspberryAPI(agv_system)

    # Executar servidor em thread separada
    import threading
    api_thread = threading.Thread(target=run_api_server, args=(api,))
    api_thread.daemon = True
    api_thread.start()

    logger.info("Servidor API iniciado em thread separada")

    # Manter thread viva
    while agv_system.running:
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Execução standalone do servidor Flask (útil para testar preview de câmera)
    logging.basicConfig(level=logging.INFO)
    try:
        from config import NETWORK_CONFIG
        port = int(NETWORK_CONFIG.get('local_port', 8080))
    except Exception:
        port = 8080

    class _DummySystem:
        running = True

    api = RaspberryAPI(_DummySystem())
    logger.info(f"API standalone iniciando em 0.0.0.0:{port}")
    api.app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)