#!/usr/bin/env python3
"""
Teste simples de câmera chinesa CSI usando Picamera2
"""

import cv2
from picamera2 import Picamera2
import time

def test_single_camera(camera_id=0):
    """Teste câmera individual"""
    print(f"📷 Testando câmera {camera_id}...")

    try:
        picam2 = Picamera2(camera_num=camera_id)
        config = picam2.create_preview_configuration(
            main={"format": 'XRGB8888', "size": (640, 480)}
        )
        picam2.configure(config)
        picam2.start()

        time.sleep(2)  # Estabilização

        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        filename = f"teste_camera_{camera_id}.jpg"
        cv2.imwrite(filename, frame_bgr)

        height, width = frame_bgr.shape[:2]
        print(f"✅ Câmera {camera_id}: {width}x{height} - {filename}")

        picam2.stop()
        return True

    except Exception as e:
        print(f"❌ Câmera {camera_id}: {e}")
        return False

def main():
    """Teste principal"""
    print("🎥 TESTE PICAMERA2 - CÂMERAS CHINESAS CSI")
    print("========================================")

    # Testar câmera 0
    cam0_ok = test_single_camera(0)

    # Testar câmera 1
    cam1_ok = test_single_camera(1)

    print("\n📊 RESULTADO:")
    print(f"Câmera 0: {'✅ OK' if cam0_ok else '❌ FALHA'}")
    print(f"Câmera 1: {'✅ OK' if cam1_ok else '❌ FALHA'}")

    if cam0_ok or cam1_ok:
        print("\n🎉 Sucesso! Use agv_camera.py no seu código AGV")
    else:
        print("\n❌ Nenhuma câmera funcionou")

if __name__ == "__main__":
    main()