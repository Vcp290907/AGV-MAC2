#!/usr/bin/env python3
"""
Leitor de QR Codes - APENAS OpenCV (Funciona Sempre)
Versão que não depende do picamera2 problemático
"""

import cv2
from pyzbar.pyzbar import decode
import time
import sys

class OpenCVOnlyQRReader:
    """Leitor que usa apenas OpenCV - funciona sempre"""

    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.qr_codes_detectados = set()

    def initialize(self):
        """Inicializar câmera OpenCV"""
        print(f"📷 Inicializando câmera OpenCV {self.camera_id}...")

        self.cap = cv2.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            print(f"❌ Não foi possível abrir câmera {self.camera_id}")
            print("💡 Verifique se uma webcam está conectada")
            return False

        # Configurar resolução
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Testar captura
        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("❌ Falha ao capturar frame de teste")
            self.cap.release()
            return False

        print("✅ Câmera OpenCV inicializada com sucesso!")
        return True

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
        """Ler QR codes usando apenas OpenCV"""
        print("🔍 LEITOR OPENCV DE QR CODES (FUNCIONA SEMPRE)")
        print("=" * 50)
        print("📷 Usando câmera OpenCV (webcam/USB)")
        print("Pressione 'q' para sair, 'r' para resetar lista")

        if not self.initialize():
            print("❌ Falha ao inicializar câmera OpenCV")
            return

        try:
            while True:
                # Capturar frame
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    print("⚠️ Frame vazio, tentando novamente...")
                    time.sleep(0.1)
                    continue

                # Detectar QR codes
                qr_codes = self.detectar_qr_codes(frame)

                # Mostrar no terminal
                if qr_codes:
                    self.mostrar_qr_codes(qr_codes)

                # Modo visual (sempre ligado para OpenCV)
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
                    info_text = f"OpenCV Camera | QR: {len(qr_codes)} | Unicos: {len(self.qr_codes_detectados)}"
                    cv2.putText(frame, info_text, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    cv2.imshow("QR Code Reader - OpenCV Only", frame)

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

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   Lista completa:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR OPENCV DE QR CODES")
    print("=" * 35)
    print("Funciona com webcam/USB - sem picamera2")

    # Verificar argumentos
    camera_id = 0
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        camera_id = int(sys.argv[1])

    print(f"📷 Usando câmera ID: {camera_id}")

    # Criar leitor OpenCV
    qr_reader = OpenCVOnlyQRReader(camera_id=camera_id)

    # Executar leitura
    qr_reader.ler_qr_codes_opencv(modo_visual=True)

if __name__ == "__main__":
    main()