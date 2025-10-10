#!/usr/bin/env python3
"""
Leitor de QR Codes que FUNCIONA com CSI
Baseado no código fornecido que funciona
"""

from picamera2 import Picamera2
import cv2
from pyzbar.pyzbar import decode
import time
import sys

class WorkingCSIQRReader:
    """Leitor CSI baseado no código que funciona"""

    def __init__(self):
        self.picam2 = None
        self.qr_codes_detectados = set()

    def initialize(self):
        """Inicializar câmera CSI como no código que funciona"""
        print("📷 Inicializando câmera CSI (método que funciona)...")

        try:
            self.picam2 = Picamera2()
            self.picam2.configure(self.picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (640, 480)}
            ))
            self.picam2.start()

            # Aguardar estabilização
            time.sleep(2)

            print("✅ Câmera CSI inicializada com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao inicializar câmera CSI: {e}")
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

    def ler_qr_codes_csi(self, modo_visual=False):
        """Ler QR codes usando câmera CSI"""
        print("🔍 LEITOR CSI DE QR CODES (VERSÃO QUE FUNCIONA)")
        print("=" * 50)
        print("Pressione 'q' para sair, 'r' para resetar lista")

        if not self.initialize():
            print("❌ Falha ao inicializar câmera CSI")
            return

        try:
            while True:
                # Capturar frame (como no código que funciona)
                frame = self.picam2.capture_array()

                # Converter de XRGB para BGR (como no código que funciona)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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

                    cv2.imshow("QR Code Reader - CSI Working", frame)

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

            if self.picam2:
                self.picam2.stop()
                print("🛑 Câmera CSI parada")

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   Lista completa:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR CSI QUE FUNCIONA")
    print("=" * 30)

    # Verificar argumentos
    modo_visual = '--visual' in sys.argv or '-v' in sys.argv

    # Criar leitor CSI
    qr_reader = WorkingCSIQRReader()

    # Executar leitura
    qr_reader.ler_qr_codes_csi(modo_visual=modo_visual)

if __name__ == "__main__":
    main()