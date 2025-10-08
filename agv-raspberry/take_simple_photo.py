#!/usr/bin/env python3
"""
Teste SIMPLES de câmera com OpenCV
Tira apenas uma foto e sai
"""

import cv2
import sys

def main():
    print("📷 TESTE SIMPLES - TIRAR UMA FOTO")
    print("=================================")

    # Tentar abrir câmera no índice 0
    print("Abrindo câmera...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Não conseguiu abrir câmera no índice 0")
        cap.release()
        sys.exit(1)

    print("✅ Câmera aberta!")

    # Aguardar um pouco para estabilizar
    import time
    time.sleep(1)

    # Tirar foto
    print("Tirando foto...")
    ret, frame = cap.read()

    if ret:
        # Salvar imagem
        filename = "foto_simples.jpg"
        cv2.imwrite(filename, frame)
        print(f"✅ Foto salva: {filename}")

        # Mostrar informações
        height, width = frame.shape[:2]
        print(f"   📐 Resolução: {width}x{height}")

        # Verificar tamanho do arquivo
        import os
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   📁 Tamanho: {size} bytes")

    else:
        print("❌ Não conseguiu tirar foto")

    # Fechar câmera
    cap.release()
    print("✅ Câmera fechada")

if __name__ == "__main__":
    main()