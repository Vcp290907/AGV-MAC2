#!/usr/bin/env python3
"""
Teste de detecção de quadrado verde
"""

import cv2
import numpy as np
from line_detector import LineDetector

def test_green_square_detection():
    print("TESTANDO DETECÇÃO DE QUADRADO VERDE")
    print("=" * 40)

    # Criar detector de linha
    detector = LineDetector()
    if not detector.initialize():
        print("❌ Falha ao inicializar detector")
        return

    # Função para detectar quadrado verde (igual à do código principal)
    def _detect_green_square(frame):
        try:
            # Converter para HSV para melhor detecção de cor
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Definir range para verde (ajuste conforme necessário)
            lower_green = np.array([35, 50, 50])   # Verde escuro
            upper_green = np.array([80, 255, 255]) # Verde claro

            # Criar máscara para verde
            mask = cv2.inRange(hsv, lower_green, upper_green)

            # Operações morfológicas para limpar a máscara
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Calcular área
                area = cv2.contourArea(contour)
                if area < 1000:  # Muito pequeno
                    continue

                # Aproximar contorno para forma geométrica
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

                # Verificar se é aproximadamente um quadrado (4 lados)
                if len(approx) == 4:
                    # Calcular bounding box
                    x, y, w, h = cv2.boundingRect(approx)

                    # Verificar proporção (deve ser aproximadamente quadrada)
                    aspect_ratio = float(w) / h
                    if 0.8 <= aspect_ratio <= 1.2:  # Proporção quadrada
                        # Verificar tamanho mínimo
                        if w > 50 and h > 50:
                            return {
                                'detected': True,
                                'bbox': (x, y, w, h),
                                'area': area,
                                'center': (x + w//2, y + h//2)
                            }

            return {'detected': False}

        except Exception as e:
            print(f"Erro na detecção de quadrado verde: {e}")
            return {'detected': False}

    print("✅ Detector inicializado")
    print("Capturando frames... (pressione Ctrl+C para parar)")

    try:
        frame_count = 0
        green_detected_count = 0

        while True:
            # Capturar frame
            line_info = detector.process_frame()

            if line_info and 'roi' in line_info:
                roi_frame = line_info['roi']
                frame_count += 1

                # Detectar quadrado verde
                green_square = _detect_green_square(roi_frame)

                if green_square['detected']:
                    green_detected_count += 1
                    bbox = green_square['bbox']
                    area = green_square['area']
                    print(f"🟢 QUADRADO VERDE DETECTADO! Frame {frame_count}")
                    print(f"   Bbox: {bbox}, Área: {area}")
                    print(f"   Centro: {green_square['center']}")
                else:
                    if frame_count % 10 == 0:  # Mostrar progresso a cada 10 frames
                        print(f"🔍 Procurando... (Frame {frame_count}, verdes detectados: {green_detected_count})")

            import time
            time.sleep(0.1)  # Pequena pausa

    except KeyboardInterrupt:
        print(f"\n🛑 Teste interrompido após {frame_count} frames")
        print(f"📊 Quadrados verdes detectados: {green_detected_count}")
    finally:
        detector.cleanup()
        print("✅ Teste finalizado")

if __name__ == "__main__":
    test_green_square_detection()