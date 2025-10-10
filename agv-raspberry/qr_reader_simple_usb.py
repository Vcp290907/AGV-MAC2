#!/usr/bin/env python3
"""
Leitor Simples de QR Codes para AGV - Versão USB/Webcam
Versão alternativa que usa OpenCV diretamente (mais compatível)
Não depende do picamera2
"""

import cv2
from pyzbar.pyzbar import decode
import time
import sys

class SimpleQRReaderUSB:
    """Leitor simples de QR codes usando webcam/USB"""

    def __init__(self, camera_id=0, width=1280, height=720):
        """Inicializar leitor simples"""
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self.qr_codes_detectados = set()  # Para evitar duplicatas

    def initialize(self):
        """Inicializar câmera USB"""
        print(f"📷 Inicializando câmera USB {self.camera_id}...")

        self.cap = cv2.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            print(f"❌ Não foi possível abrir câmera {self.camera_id}")
            print("💡 Verifique se a câmera está conectada e não está sendo usada por outro programa")
            return False

        # Configurar resolução
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Testar captura
        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("❌ Falha ao capturar frame de teste")
            self.cap.release()
            return False

        print(f"✅ Câmera USB {self.camera_id} inicializada: {self.width}x{self.height}")
        return True

    def detectar_qr_codes(self, frame):
        """Detectar QR codes em um frame"""
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

    def ler_qr_codes_simples(self, modo_visual=False):
        """Ler QR codes de forma simples"""
        print("🔍 LEITOR SIMPLES DE QR CODES (USB)")
        print("=" * 40)
        print("📷 Usando câmera USB/webcam...")
        print("Pressione 'q' para sair, 'r' para resetar lista")

        if not self.initialize():
            print("❌ Falha ao inicializar câmera USB")
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

                # Modo visual opcional
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
                    info_text = f"QR Codes: {len(qr_codes)} | Unicos: {len(self.qr_codes_detectados)}"
                    cv2.putText(frame, info_text, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    cv2.imshow("QR Code Reader - USB Camera", frame)

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
                print("🛑 Câmera USB liberada")

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   Lista completa:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR SIMPLES DE QR CODES (USB)")
    print("=" * 40)

    # Verificar argumentos
    modo_visual = '--visual' in sys.argv or '-v' in sys.argv

    # Criar leitor
    qr_reader = SimpleQRReaderUSB(camera_id=0, width=1280, height=720)

    # Executar leitura
    qr_reader.ler_qr_codes_simples(modo_visual=modo_visual)

if __name__ == "__main__":
    main()