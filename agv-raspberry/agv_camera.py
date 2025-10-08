#!/usr/bin/env python3
"""
Módulo de câmera para AGV usando Picamera2
Suporte para múltiplas câmeras chinesas CSI
"""

import cv2
import os
from picamera2 import Picamera2
import time

class AGVCamera:
    def __init__(self, camera_id=0, width=640, height=480):
        """Inicializar câmera AGV"""
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.picam2 = None
        self.initialized = False

    def initialize(self):
        """Inicializar a câmera"""
        try:
            print(f"📷 Inicializando câmera {self.camera_id}...")
            self.picam2 = Picamera2(camera_num=self.camera_id)

            # Configuração para câmeras chinesas CSI
            config = self.picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (self.width, self.height)}
            )
            self.picam2.configure(config)

            self.picam2.start()
            time.sleep(2)  # Aguardar estabilização

            self.initialized = True
            print(f"✅ Câmera {self.camera_id} inicializada: {self.width}x{self.height}")

        except Exception as e:
            print(f"❌ Erro ao inicializar câmera {self.camera_id}: {e}")
            self.initialized = False

    def capture_frame(self):
        """Capturar um frame da câmera"""
        if not self.initialized:
            return None

        try:
            frame = self.picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame_bgr
        except Exception as e:
            print(f"❌ Erro ao capturar frame câmera {self.camera_id}: {e}")
            return None

    def release(self):
        """Liberar câmera"""
        if self.picam2:
            self.picam2.stop()
            print(f"🛑 Câmera {self.camera_id} liberada")
        self.initialized = False

class AGVDualCamera:
    """Sistema de duas câmeras para AGV"""
    def __init__(self, width=640, height=480):
        self.camera1 = AGVCamera(camera_id=0, width=width, height=height)
        self.camera2 = AGVCamera(camera_id=1, width=width, height=height)

    def initialize(self):
        """Inicializar ambas as câmeras"""
        print("🚗 Inicializando sistema dual de câmeras AGV...")
        self.camera1.initialize()
        self.camera2.initialize()

        if self.camera1.initialized or self.camera2.initialized:
            print("✅ Pelo menos uma câmera inicializada")
        else:
            print("❌ Nenhuma câmera pôde ser inicializada")

    def capture_frames(self):
        """Capturar frames de ambas as câmeras"""
        frame1 = self.camera1.capture_frame() if self.camera1.initialized else None
        frame2 = self.camera2.capture_frame() if self.camera2.initialized else None
        return frame1, frame2

    def capture_stereo(self):
        """Capturar par estereo para visão 3D"""
        frame1, frame2 = self.capture_frames()
        if frame1 is not None and frame2 is not None:
            return frame1, frame2
        else:
            print("⚠️ Sistema estéreo incompleto")
            return frame1, frame2

    def release(self):
        """Liberar ambas as câmeras"""
        self.camera1.release()
        self.camera2.release()

# Exemplo de uso
if __name__ == "__main__":
    # Sistema dual de câmeras
    dual_camera = AGVDualCamera(width=640, height=480)

    try:
        dual_camera.initialize()

        # Capturar algumas imagens de teste
        for i in range(3):
            frame1, frame2 = dual_camera.capture_frames()

            if frame1 is not None:
                cv2.imwrite(f"camera1_test_{i+1}.jpg", frame1)
                print(f"💾 Câmera 1: camera1_test_{i+1}.jpg")

            if frame2 is not None:
                cv2.imwrite(f"camera2_test_{i+1}.jpg", frame2)
                print(f"💾 Câmera 2: camera2_test_{i+1}.jpg")

            time.sleep(1)

        print("✅ Teste do sistema dual de câmeras concluído!")

    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")

    finally:
        dual_camera.release()