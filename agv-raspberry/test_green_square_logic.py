#!/usr/bin/env python3
"""
Teste da lógica de detecção de quadrado verde
"""

import numpy as np
import cv2

def _detect_green_square(frame):
    """Detectar quadrado verde no frame"""
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

def test_green_square_logic():
    """Testar a lógica de detecção de quadrado verde"""
    print("🧪 Testando lógica de detecção de quadrado verde")

    # Criar um frame de teste com um quadrado verde
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Desenhar um quadrado verde no centro
    cv2.rectangle(frame, (270, 190), (370, 290), (0, 255, 0), -1)  # Verde

    # Testar detecção
    result = _detect_green_square(frame)

    if result['detected']:
        print("✅ Quadrado verde detectado com sucesso!")
        print(f"   Bounding box: {result['bbox']}")
        print(f"   Centro: {result['center']}")
        print(f"   Área: {result['area']}")

        # Testar expansão do ROI
        x, y, w, h = result['bbox']
        margin = 80  # Margem maior
        x_start = max(0, x - margin)
        y_start = max(0, y - margin)
        x_end = min(frame.shape[1], x + w + margin)
        y_end = min(frame.shape[0], y + h + margin)

        print(f"   ROI expandido: ({x_start}, {y_start}) to ({x_end}, {y_end})")
        print(f"   Tamanho do ROI: {(x_end - x_start)}x{(y_end - y_start)}")

        return True
    else:
        print("❌ Quadrado verde não detectado")
        return False

if __name__ == "__main__":
    test_green_square_logic()