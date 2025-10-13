#!/usr/bin/env python3
"""
Debug da detecção de quadrado verde
"""

import cv2
import numpy as np

def debug_green_detection():
    """Debug da detecção de cor verde"""

    print("🔍 DEBUG DETECÇÃO DE QUADRADO VERDE")
    print("=" * 50)

    # Criar frame de teste
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Desenhar quadrado verde grande no centro (quadrado perfeito)
    cv2.rectangle(frame, (250, 150), (410, 310), (0, 255, 0), -1)  # 160x160 pixels - quadrado perfeito

    # Adicionar texto
    cv2.putText(frame, "VERDE", (300, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    print("🟢 Frame criado com quadrado verde grande")

    # Verificar valores RGB no centro
    center_pixel = frame[240, 320]  # Centro do frame
    print(f"📊 Pixel central RGB: {center_pixel}")

    # Converter para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    center_hsv = hsv[240, 320]
    print(f"📊 Pixel central HSV: {center_hsv}")

    # Testar diferentes ranges de verde
    ranges_to_test = [
        ("Conservador", np.array([35, 50, 50]), np.array([80, 255, 255])),
        ("Permissivo", np.array([30, 30, 30]), np.array([90, 255, 255])),
        ("Muito permissivo", np.array([25, 20, 20]), np.array([100, 255, 255])),
    ]

    for name, lower, upper in ranges_to_test:
        print(f"\n🔍 Testando range: {name}")
        print(f"   Lower: {lower}, Upper: {upper}")

        mask = cv2.inRange(hsv, lower, upper)

        # Verificar se o centro está na máscara
        center_mask = mask[240, 320]
        print(f"   Centro na máscara: {center_mask}")

        # Contar pixels na máscara
        total_pixels = cv2.countNonZero(mask)
        print(f"   Pixels verdes detectados: {total_pixels}")

        if total_pixels > 1000:
            print("   ✅ DETECÇÃO BEM SUCEDIDA!")
            # Testar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            print(f"   Contornos encontrados: {len(contours)}")

            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 1000:
                    print(f"   Contorno {i}: área = {area}")
                    x, y, w, h = cv2.boundingRect(contour)
                    print(f"   Bounding box: ({x}, {y}, {w}, {h})")

                    # Verificar se é quadrado
                    aspect_ratio = float(w) / h
                    print(f"   Aspect ratio: {aspect_ratio:.2f}")

                    if 0.8 <= aspect_ratio <= 1.2 and w > 50 and h > 50:
                        print("   ✅ QUADRADO VERDE DETECTADO!")
                        return True

    print("\n❌ Nenhum range conseguiu detectar o quadrado verde")
    return False

if __name__ == "__main__":
    debug_green_detection()