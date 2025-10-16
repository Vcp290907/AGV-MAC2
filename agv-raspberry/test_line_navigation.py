#!/usr/bin/env python3
"""
Teste direto do detector de linha durante navegação
Reproduz exatamente o que acontece no line_following_navigation.py
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from line_detector import LineDetector

def test_line_detection_during_navigation():
    """Testar detecção de linha exatamente como na navegação"""
    print("🔍 TESTE DIRETO DO DETECTOR DE LINHA DURANTE NAVEGAÇÃO")
    print("=" * 60)

    # Criar detector exatamente como na navegação
    detector = LineDetector()

    # Inicializar exatamente como na navegação
    if not detector.initialize():
        print("❌ Falha na inicialização")
        return

    try:
        print("📷 Testando detecção de linha (como na navegação)...")

        for i in range(5):
            print(f"\n--- Teste {i+1} ---")

            # Chamar process_frame exatamente como na navegação
            print("Chamando detector.process_frame()...")
            line_info = detector.process_frame()
            print(f"Resultado de process_frame(): {line_info}")

            if not line_info:
                print("❌ line_info é None - debug do que aconteceu:")

                # Testar capture_frame diretamente
                print("Testando capture_frame()...")
                frame = detector.capture_frame()
                print(f"capture_frame() retornou: {frame is not None}")
                if frame is not None:
                    print(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")

                # Testar preprocess_image se frame foi capturado
                if frame is not None:
                    print("Testando preprocess_image()...")
                    mask, roi, frame_bgr = detector.preprocess_image(frame)
                    print(f"preprocess_image() retornou mask: {mask is not None}")
                    if mask is not None:
                        print(f"Mask shape: {mask.shape}")

                continue

            detected = line_info.get('detected', False)
            print(f"Resultado: detected = {detected}")

            if not detected:
                print("⚠️ Linha não detectada - parando (mesmo erro da navegação)")
                # Mostrar debug info
                if 'debug_black_ratio' in line_info:
                    print(f"Debug: black_ratio = {line_info['debug_black_ratio']:.2%}")

                # Verificar se há máscara para debug
                if 'mask' in line_info:
                    import cv2
                    black_pixels = cv2.countNonZero(line_info['mask'])
                    total_pixels = line_info['mask'].size
                    print(f"Debug: pixels pretos na máscara = {black_pixels}/{total_pixels} ({black_pixels/total_pixels:.2%})")
            else:
                print("✅ Linha detectada!")
                print(f"Centro: {line_info.get('center', 'N/A')}, Largura: {line_info.get('width', 'N/A')}")

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

    finally:
        detector.cleanup()

if __name__ == "__main__":
    test_line_detection_during_navigation()