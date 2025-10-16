#!/usr/bin/env python3
"""
Leitor de QR Codes - Picamera2 Only
Versão que usa apenas Picamera2 para consistência
"""

import cv2
from pyzbar.pyzbar import decode
import time
import sys
import threading

# Gerenciador global de câmera para evitar conflitos
_camera_managers = {}  # Dicionário por camera_id
_camera_lock = threading.Lock()

def get_camera_manager(camera_id=1):
    """Obter instância singleton do gerenciador de câmera por camera_id"""
    global _camera_managers
    with _camera_lock:
        if camera_id not in _camera_managers:
            _camera_managers[camera_id] = CameraManager(camera_id)
        return _camera_managers[camera_id]

class CameraManager:
    """Gerenciador singleton para Picamera2"""
    
    def __init__(self, camera_id=1):
        self.camera_id = camera_id
        self.picam2 = None
        self.initialized = False
        self.lock = threading.Lock()
        
    def initialize(self):
        """Inicializar câmera se ainda não foi inicializada"""
        with self.lock:
            if self.initialized:
                return True
                
            try:
                from picamera2 import Picamera2
                self.picam2 = Picamera2(self.camera_id)
                # Definir resolução por câmera: cam 0 (shelf/QR) em alta resolução 3280x2464
                # Observação: Picamera2 usa (width, height). Mantemos cam 1 no padrão atual.
                desired_sizes = {
                    0: (3280, 2464),  # Cam 0: alta resolução (IMX219 full)
                }
                size = desired_sizes.get(int(self.camera_id), (720, 1024))
                # Garantir tupla (w,h)
                if isinstance(size, (list, tuple)) and len(size) == 2:
                    w, h = int(size[0]), int(size[1])
                else:
                    w, h = 720, 1024
                config = self.picam2.create_still_configuration(
                    main={"format": 'RGB888', "size": (w, h)}
                )
                self.picam2.configure(config)
                self.initialized = True
                print(f"📷 Camera Manager inicializado (câmera {self.camera_id})")
                return True
            except Exception as e:
                print(f"Erro ao inicializar Camera Manager: {e}")
                return False
    
    def capture_frame(self):
        """Capturar um frame da câmera"""
        if not self.initialized:
            return None
            
        with self.lock:
            try:
                self.picam2.start()
                frame = self.picam2.capture_array()
                self.picam2.stop()
                return frame
            except Exception as e:
                print(f"❌ Erro ao capturar frame: {e}")
                return None

class OpenCVOnlyQRReader:
    """Leitor que usa apenas Picamera2 para consistência"""

    def detectar_qr_code(self):
        """Detectar um único QR code para navegação"""
        try:
            # Verificar se a câmera está inicializada
            if self.camera_manager is None:
                if not self.initialize():
                    return {
                        'detectado': False,
                        'codigo': None,
                        'erro': 'Câmera não inicializada',
                        'timestamp': time.time()
                    }

            # Usar CameraManager para capturar frame
            try:
                frame = self.camera_manager.capture_frame()
                if frame is None:
                    return {
                        'detectado': False,
                        'codigo': None,
                        'erro': 'Falha ao capturar frame',
                        'timestamp': time.time()
                    }
                # Converter RGB para BGR para compatibilidade com pyzbar
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                return {
                    'detectado': False,
                    'codigo': None,
                    'erro': f'Falha CameraManager: {e}',
                    'timestamp': time.time()
                }

            # Detectar QR codes
            qr_codes = self.detectar_qr_codes(frame)

            if qr_codes:
                # Retornar o primeiro QR code detectado
                qr = qr_codes[0]
                return {
                    'detectado': True,
                    'codigo': qr['data'],
                    'bbox': qr['bbox'],
                    'timestamp': time.time()
                }
            else:
                return {
                    'detectado': False,
                    'codigo': None,
                    'timestamp': time.time()
                }

        except Exception as e:
            return {
                'detectado': False,
                'codigo': None,
                'erro': str(e),
                'timestamp': time.time()
            }

    def __init__(self, camera_id=0):
        # Usar CameraManager para evitar conflitos
        self.camera_id = camera_id
        self.cap = None  # Não usar OpenCV
        self.camera_manager = None  # Usar CameraManager
        self.qr_codes_detectados = set()

    def initialize(self):
        """Inicializar câmera usando CameraManager"""
        print(f"Inicializando camera Picamera2 {self.camera_id}...")

        try:
            # Usar CameraManager para evitar conflitos
            self.camera_manager = get_camera_manager(self.camera_id)
            success = self.camera_manager.initialize()
            
            if success:
                print("Camera Picamera2 inicializada com sucesso!")
                return True
            else:
                print("Falha ao inicializar Camera Manager")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao inicializar Picamera2: {e}")
            print("Sistema continuara sem camera - use apenas navegacao basica")
            return False

    def detectar_qr_codes(self, frame):
        """Detectar QR codes no frame"""
        try:
            decoded_objects = decode(frame)
            qr_codes = []

            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                qr_codes.append({
                    'data': data,
                    'bbox': obj.rect,
                    'type': obj.type
                })

            return qr_codes

        except Exception as e:
            print(f"❌ Erro ao detectar QR codes: {e}")
            return []

    def mostrar_qr_codes(self, qr_codes):
        """Mostrar QR codes detectados"""
        if not qr_codes:
            return

        print(f"\n🎯 QR CODES DETECTADOS ({len(qr_codes)}):")
        print("-" * 40)

        for i, qr in enumerate(qr_codes, 1):
            data = qr['data']
            if data not in self.qr_codes_detectados:
                self.qr_codes_detectados.add(data)
                print(f"✅ QR {i}: {data}")
            else:
                print(f"🔄 QR {i}: {data} (já detectado)")

    def ler_qr_codes_opencv(self, modo_visual=True):
        """Ler QR codes usando OpenCV ou Picamera2"""
        print("🔍 LEITOR DE QR CODES (OpenCV + Picamera2 fallback)")
        print("=" * 55)
        print("📷 Usando câmera OpenCV ou Picamera2")
        print("Pressione 'q' para sair, 'r' para resetar lista")

        if not self.initialize():
            print("❌ Falha ao inicializar câmera")
            return

        try:
            while True:
                # Capturar frame
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        print("⚠️ Frame vazio, tentando novamente...")
                        time.sleep(0.1)
                        continue
                elif self.picam2:
                    try:
                        self.picam2.start()
                        frame = self.picam2.capture_array()
                        self.picam2.stop()
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    except Exception as e:
                        print(f"⚠️ Erro Picamera2: {e}")
                        time.sleep(0.1)
                        continue
                else:
                    print("⚠️ Nenhuma câmera disponível")
                    time.sleep(0.1)
                    continue

                # Detectar QR codes
                qr_codes = self.detectar_qr_codes(frame)

                # Mostrar no terminal
                if qr_codes:
                    self.mostrar_qr_codes(qr_codes)

                # Modo visual
                if modo_visual:
                    # Desenhar detecções
                    for qr in qr_codes:
                        bbox = qr['bbox']
                        cv2.rectangle(frame, (bbox.left, bbox.top),
                                    (bbox.left + bbox.width, bbox.top + bbox.height),
                                    (0, 255, 0), 3)

                        # Mostrar texto
                        text = qr['data'][:30] + "..." if len(qr['data']) > 30 else qr['data']
                        cv2.putText(frame, text, (bbox.left, bbox.top - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # Mostrar estatísticas
                    camera_type = "OpenCV" if self.cap and self.cap.isOpened() else "Picamera2"
                    info_text = f"{camera_type} Camera | QR: {len(qr_codes)} | Unicos: {len(self.qr_codes_detectados)}"
                    cv2.putText(frame, info_text, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    cv2.imshow("QR Code Reader - OpenCV + Picamera2", frame)

                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.qr_codes_detectados.clear()
                    print("🔄 Lista de QR codes resetada")

                time.sleep(0.1)  # Pequena pausa

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")

        finally:
            if modo_visual:
                cv2.destroyAllWindows()

            if self.cap:
                self.cap.release()
                print("🛑 Câmera OpenCV liberada")
            if self.picam2:
                try:
                    self.picam2.stop()
                except:
                    pass
                print("🛑 Câmera Picamera2 liberada")

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   Lista completa:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR DE QR CODES (OpenCV + Picamera2)")
    print("=" * 45)
    print("Funciona com webcam/USB ou câmera CSI - com fallback")

    # Verificar argumentos
    camera_id = 0
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        camera_id = int(sys.argv[1])

    print(f"📷 Usando câmera ID: {camera_id}")

    # Criar leitor com fallback
    qr_reader = OpenCVOnlyQRReader(camera_id=camera_id)

    # Executar leitura
    qr_reader.ler_qr_codes_opencv(modo_visual=True)

if __name__ == "__main__":
    main()