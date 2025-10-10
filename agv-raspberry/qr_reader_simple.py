#!/usr/bin/env python3
"""
Leitor Simples de QR Codes para AGV
Baseado no sistema de câmera existente
Apenas lê QR codes e mostra o conteúdo
"""

import cv2
from pyzbar.pyzbar import decode
from agv_camera import AGVCamera
import time
import sys

class SimpleQRReader:
    """Leitor simples de QR codes"""

    def __init__(self, camera_id=0, width=1280, height=720):
        """Inicializar leitor simples"""
        self.camera = AGVCamera(camera_id=camera_id, width=width, height=height)
        self.qr_codes_detectados = set()  # Para evitar duplicatas

    def initialize(self):
        """Inicializar câmera"""
        print("📷 Inicializando câmera para leitura de QR codes...")
        return self.camera.initialize()

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
        print("🔍 LEITOR SIMPLES DE QR CODES")
        print("=" * 35)
        print("📷 Lendo QR codes e mostrando conteúdo...")
        print("Pressione 'q' para sair, 'r' para resetar lista")

        if not self.initialize():
            print("❌ Falha ao inicializar câmera")
            return

        try:
            while True:
                # Capturar frame
                frame = self.camera.capture_frame()

                if frame is None:
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

                    cv2.imshow("QR Code Reader", frame)

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
            self.camera.release()

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   Lista completa:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR SIMPLES DE QR CODES PARA AGV")
    print("=" * 40)

    # Verificar argumentos
    modo_visual = '--visual' in sys.argv or '-v' in sys.argv

    # Criar leitor
    qr_reader = SimpleQRReader(camera_id=0, width=1280, height=720)

    # Executar leitura
    qr_reader.ler_qr_codes_simples(modo_visual=modo_visual)

if __name__ == "__main__":
    main()