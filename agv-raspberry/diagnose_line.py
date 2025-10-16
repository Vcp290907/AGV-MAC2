#!/usr/bin/env python3
"""
Diagnóstico de Detecção de Linha - Teste em Tempo Real
"""

import cv2
import numpy as np
from picamera2 import Picamera2
import time

def test_line_detection():
    print("🔍 DIAGNÓSTICO DE DETECÇÃO DE LINHA")
    print("=" * 50)

    # Inicializar câmera
    try:
        picam2 = Picamera2(1)  # Câmera 1 para detecção de linha
        config = picam2.create_still_configuration(main={'format': 'RGB888', 'size': (720, 1024)})
        picam2.configure(config)
        picam2.start()
        print("✅ Câmera 1 inicializada")
    except Exception as e:
        print(f"❌ Erro ao inicializar câmera: {e}")
        return

    try:
        for frame_num in range(10):
            print(f"\n--- Frame {frame_num + 1} ---")

            # Capturar frame
            frame = picam2.capture_array()
            print(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")

            # Estatísticas básicas
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

            print(f"Média RGB: R={np.mean(frame[:,:,0]):.1f}, G={np.mean(frame[:,:,1]):.1f}, B={np.mean(frame[:,:,2]):.1f}")
            print(f"Média HSV: H={np.mean(hsv[:,:,0]):.1f}, S={np.mean(hsv[:,:,1]):.1f}, V={np.mean(hsv[:,:,2]):.1f}")

            # Definir thresholds para teste
            thresholds = [
                ([0, 0, 0], [180, 255, 120], "Original"),
                ([0, 0, 0], [180, 255, 200], "Permissivo"),
                ([0, 0, 50], [180, 255, 255], "Muito permissivo"),
                ([0, 0, 100], [180, 50, 255], "Alto contraste"),
                ([0, 0, 0], [180, 100, 150], "Contraste médio"),
                ([0, 0, 30], [180, 255, 180], "Balanceado"),
            ]

            # Focar no ROI usado pelo detector de linha (30% inferior)
            height, width = frame.shape[:2]
            roi_y_start = int(height * 0.3)  # 30% da altura
            roi = frame_bgr[roi_y_start:, :]  # Parte inferior da imagem
            roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            print(f"ROI: y={roi_y_start} até y={height} (altura={roi.shape[0]})")
            
            # Testar thresholds no ROI
            for lower, upper, name in thresholds:
                mask = cv2.inRange(roi_hsv, np.array(lower), np.array(upper))
                black_pixels = cv2.countNonZero(mask)
                total_pixels = mask.size
                ratio = black_pixels / total_pixels
                
                print(f"  {name} (ROI): {black_pixels}/{total_pixels} ({ratio:.2%})")
                
                # Se encontrou pixels pretos suficientes, analisar contornos
                if ratio > 0.01:  # Mais de 1%
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        largest = max(contours, key=cv2.contourArea)
                        area = cv2.contourArea(largest)
                        x, y, w, h = cv2.boundingRect(largest)
                        print(f"    Maior contorno (ROI): área={area}, bbox=({x},{y},{w},{h})")
                        
                        # Verificar se atende aos critérios do detector
                        min_width = 2
                        if w >= min_width:
                            print(f"    ✅ ATENDE CRITÉRIOS: largura {w} >= {min_width}")
                        else:
                            print(f"    ❌ NÃO ATENDE: largura {w} < {min_width}")
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                black_pixels = cv2.countNonZero(mask)
                total_pixels = mask.size
                ratio = black_pixels / total_pixels

                print(f"{name}: {black_pixels}/{total_pixels} ({ratio:.2%})")

                # Se encontrou pixels pretos suficientes, mostrar mais detalhes
                if ratio > 0.01:  # Mais de 1%
                    # Aplicar morfologia
                    kernel = np.ones((3, 3), np.uint8)
                    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                    mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)

                    # Encontrar contornos
                    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if contours:
                        # Maior contorno
                        largest = max(contours, key=cv2.contourArea)
                        area = cv2.contourArea(largest)
                        x, y, w, h = cv2.boundingRect(largest)

                        print(f"  → Contorno encontrado: área={area:.0f}, bbox=({x},{y},{w},{h})")

                        if w >= 2:  # Largura mínima
                            print(f"  ✅ POSSÍVEL LINHA DETECTADA com threshold '{name}'!")
                    else:
                        print(f"  → Nenhum contorno encontrado")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
    finally:
        picam2.stop()
        print("✅ Teste concluído")

if __name__ == "__main__":
    test_line_detection()