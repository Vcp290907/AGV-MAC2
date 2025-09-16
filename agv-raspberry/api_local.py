#!/usr/bin/env python3
"""
API Local do Raspberry Pi
Fornece endpoints REST para comunicação com o sistema PC
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import json
from datetime import datetime
import asyncio
import threading

logger = logging.getLogger(__name__)

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
                    'GET /camera - Stream da câmera',
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
                    'available': True,
                    'resolution': '640x480',
                    'fps': 30,
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
            logger.info(f"Executando movimento: {direction} por {duration}s")

            # TODO: Implementar comunicação real com ESP32
            # Por enquanto, apenas simular o movimento

            # Simulação de movimento
            import time
            time.sleep(duration)  # Simular tempo de movimento

            # Simular sucesso
            result = {
                'success': True,
                'message': f'Movimento {direction} executado por {duration} segundos',
                'direction': direction,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Movimento simulado concluído: {result['message']}")
            return result

        except Exception as e:
            logger.error(f"Erro ao executar movimento {direction}: {e}")
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