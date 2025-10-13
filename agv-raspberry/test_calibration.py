#!/usr/bin/env python3
"""
Teste rápido da calibração do quadrado verde
"""

import cv2
import numpy as np

def test_calibration_interface():
    """Testar interface de calibração"""

    print("🧪 TESTANDO INTERFACE DE CALIBRAÇÃO")
    print("=" * 40)

    # Simular parâmetros
    params = {
        'h_min': 30, 'h_max': 90,
        's_min': 30, 's_max': 255,
        'v_min': 30, 'v_max': 255,
        'min_size': 50
    }

    # Criar frame de teste
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Desenhar alguns quadrados verdes de diferentes tamanhos
    cv2.rectangle(frame, (100, 100), (150, 150), (0, 255, 0), -1)  # Pequeno
    cv2.rectangle(frame, (200, 200), (280, 280), (0, 255, 0), -1)  # Médio
    cv2.rectangle(frame, (350, 150), (450, 250), (0, 255, 0), -1)  # Grande

    # Adicionar texto
    cv2.putText(frame, "TESTE CALIBRACAO", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    print("🟢 Frame de teste criado com 3 quadrados verdes de diferentes tamanhos")

    # Simular detecção
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([params['h_min'], params['s_min'], params['v_min']])
    upper = np.array([params['h_max'], params['s_max'], params['v_max']])
    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result_frame = frame.copy()
    detected = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h

                if 0.7 <= aspect_ratio <= 1.4 and w > params['min_size'] and h > params['min_size']:
                    cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(result_frame, f"{w}x{h}", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    detected += 1

    print(f"✅ Detectados {detected} quadrados verdes com parâmetros atuais")

    # Mostrar resultado
    cv2.imshow("Resultado Calibracao", result_frame)
    cv2.imshow("Mascara", mask)

    print("📋 Instruções de calibração:")
    print("  H - Ajustar Hue (matiz)")
    print("  S - Ajustar Saturation (saturação)")
    print("  V - Ajustar Value (brilho)")
    print("  T - Ajustar tamanho mínimo")
    print("  R - Reset para padrão")
    print("  ESC - Sair")

    print("\n🔧 Parâmetros atuais:")
    print(f"   Hue: {params['h_min']}-{params['h_max']}")
    print(f"   Saturation: {params['s_min']}-{params['s_max']}")
    print(f"   Value: {params['v_min']}-{params['v_max']}")
    print(f"   Tamanho mínimo: {params['min_size']}")

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("✅ Teste da interface de calibração concluído")

if __name__ == "__main__":
    test_calibration_interface()