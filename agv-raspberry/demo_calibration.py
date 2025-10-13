#!/usr/bin/env python3
"""
Demonstração da interface de calibração do quadrado verde
"""

import cv2
import numpy as np

def demo_calibration_interface():
    """Demonstrar interface de calibração com trackbars"""

    print("🎨 DEMONSTRAÇÃO - INTERFACE DE CALIBRAÇÃO HSV")
    print("=" * 50)
    print("Esta é uma demonstração da interface que será usada")
    print("para calibrar a detecção do quadrado verde.")
    print()
    print("Recursos da interface:")
    print("• Janela 'Controles HSV' com 6 trackbars deslizantes")
    print("• Janela principal dividida: Original + Máscara")
    print("• Detecção em tempo real de quadrados verdes")
    print("• Contadores e parâmetros exibidos na tela")
    print()
    print("Controles:")
    print("• H Min/Max: Controla a matiz (tonalidade)")
    print("• S Min/Max: Controla a saturação (intensidade)")
    print("• V Min/Max: Controla o brilho (luminosidade)")
    print("• ESC: Salva e sai da calibração")
    print()

    # Criar frame de demonstração
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Adicionar alguns elementos visuais
    cv2.putText(frame, "DEMONSTRACAO - CALIBRACAO VERDE", (50, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.putText(frame, "Posicione um quadrado verde", (50, 100),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.putText(frame, "na frente da camera e ajuste", (50, 130),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.putText(frame, "os controles ate detectar", (50, 160),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Desenhar exemplo de quadrado verde
    cv2.rectangle(frame, (400, 200), (500, 300), (0, 255, 0), -1)
    cv2.putText(frame, "EXEMPLO", (410, 250),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    # Simular máscara
    mask = np.zeros((480, 640), dtype=np.uint8)
    cv2.rectangle(mask, (400, 200), (500, 300), 255, -1)

    # Mostrar demonstração
    cv2.imshow("Demonstracao - Interface de Calibracao", frame)
    cv2.imshow("Mascara Verde (exemplo)", mask)

    print("Pressione qualquer tecla para fechar a demonstração...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("✅ Demonstração concluída!")
    print()
    print("Para usar a calibração real:")
    print("1. Execute: python3 line_following_navigation.py")
    print("2. Escolha opção 10: 'Calibrar quadrado verde'")
    print("3. Ajuste os trackbars até detectar seu quadrado verde")
    print("4. Pressione ESC para salvar")

if __name__ == "__main__":
    demo_calibration_interface()