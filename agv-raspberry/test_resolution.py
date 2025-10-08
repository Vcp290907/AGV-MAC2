#!/usr/bin/env python3
"""
Teste das resoluções das câmeras AGV
"""

from agv_camera import AGVDualCamera

def main():
    print("📐 TESTE DE RESOLUÇÃO - CÂMERAS AGV")
    print("===================================")

    # Sistema dual com resoluções diferentes
    camera = AGVDualCamera(width1=640, height1=480, width2=1280, height2=720)

    try:
        camera.initialize()

        # Capturar frames
        frame1, frame2 = camera.capture_frames()

        print("📊 RESOLUÇÕES CAPTURADAS:")

        if frame1 is not None:
            h1, w1 = frame1.shape[:2]
            print(f"✅ Câmera 1: {w1}x{h1} (configurada: 640x480)")
        else:
            print("❌ Câmera 1: Falha na captura")

        if frame2 is not None:
            h2, w2 = frame2.shape[:2]
            print(f"✅ Câmera 2: {w2}x{h2} (configurada: 1280x720)")
        else:
            print("❌ Câmera 2: Falha na captura")

        if frame1 is not None and frame2 is not None:
            print("
🎯 DIFERENÇA DE RESOLUÇÃO:"            print(f"   Câmera 2 tem {w2/w1:.1f}x mais largura e {h2/h1:.1f}x mais altura")
            print("   Câmera 2 oferece ~2.25x mais pixels!")

    except Exception as e:
        print(f"❌ Erro: {e}")

    finally:
        camera.release()

if __name__ == "__main__":
    main()