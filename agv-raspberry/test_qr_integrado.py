#!/usr/bin/env python3
"""
Teste de detecção de QR codes integrado
"""

from line_detector import LineDetector
from pyzbar.pyzbar import decode
import time

def test_qr_detection():
    print("TESTANDO DETECÇÃO DE QR CODES INTEGRADA")
    print("=" * 45)

    # Inicializar detector de linha
    detector = LineDetector()
    if not detector.initialize():
        print("❌ Falha ao inicializar detector")
        return

    print("✅ Detector inicializado")
    print("Aponte a câmera para um QR code...")
    print("Pressione Ctrl+C para sair")

    try:
        while True:
            # Capturar frame
            line_info = detector.process_frame()

            if line_info and 'roi' in line_info:
                roi_frame = line_info['roi']

                # Tentar detectar QR codes
                qr_codes = decode(roi_frame)

                if qr_codes:
                    for qr in qr_codes:
                        data = qr.data.decode('utf-8')
                        print(f"🎯 QR CODE DETECTADO: {data}")
                        print(f"   Tipo: {qr.type}")
                        print(f"   Bbox: {qr.rect}")

                        # Verificar se é subcorredor
                        if data.startswith('Corredor') and '_' in data:
                            print(f"🏢 SUBCORREDOR IDENTIFICADO: {data}")
                else:
                    print("🔍 Procurando QR codes...")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido")
    finally:
        detector.cleanup()
        print("✅ Teste finalizado")

if __name__ == "__main__":
    test_qr_detection()