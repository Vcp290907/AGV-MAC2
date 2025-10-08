#!/usr/bin/env python3
"""
Módulo de câmera para AGV usando Picamera2
Compatível com câmeras chinesas CSI
"""

import cv2
import os
from picamera2 import Picamera2
import time

class AGVCamera:
    def __init__(self, width=640, height=480):
        """Inicializar câmera AGV"""
        self.width = width
        self.height = height
        self.picam2 = None
        self.initialized = False

    def initialize(self):
        """Inicializar a câmera"""
        try:
            print("📷 Inicializando câmera AGV...")
            self.picam2 = Picamera2()

            # Configuração para câmeras chinesas CSI
            config = self.picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (self.width, self.height)}
            )
            self.picam2.configure(config)

            self.picam2.start()
            time.sleep(2)  # Aguardar estabilização

            self.initialized = True
            print(f"✅ Câmera AGV inicializada: {self.width}x{self.height}")

        except Exception as e:
            print(f"❌ Erro ao inicializar câmera: {e}")
            self.initialized = False

    def capture_frame(self):
        """Capturar um frame da câmera"""
        if not self.initialized:
            print("❌ Câmera não inicializada")
            return None

        try:
            # Capturar frame
            frame = self.picam2.capture_array()

            # Converter formato para OpenCV (XRGB para BGR)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            return frame_bgr

        except Exception as e:
            print(f"❌ Erro ao capturar frame: {e}")
            return None

    def capture_and_save(self, filename="agv_capture.jpg"):
        """Capturar e salvar imagem"""
        frame = self.capture_frame()
        if frame is not None:
            cv2.imwrite(filename, frame)
            print(f"💾 Imagem salva: {filename}")
            return True
        return False

    def release(self):
        """Liberar câmera"""
        if self.picam2:
            self.picam2.stop()
            print("🛑 Câmera AGV liberada")
        self.initialized = False

# Exemplo de uso
if __name__ == "__main__":
    # Criar instância da câmera
    camera = AGVCamera(width=640, height=480)

    try:
        # Inicializar
        camera.initialize()

        if camera.initialized:
            # Capturar algumas imagens de teste
            for i in range(3):
                filename = f"agv_test_{i+1}.jpg"
                camera.capture_and_save(filename)
                time.sleep(1)

            print("✅ Teste da câmera AGV concluído!")

    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")

    finally:
        # Sempre liberar a câmera
        camera.release()