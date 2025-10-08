#!/usr/bin/env python3
"""
Teste rápido do sistema dual de câmeras AGV
"""

from agv_camera import AGVDualCamera
import time

def main():
    """Teste do sistema dual camera"""
    print("🧪 TESTE SISTEMA DUAL CAMERA AGV")
    print("===============================")

    # Inicializar sistema dual com resoluções diferentes
    dual_camera = AGVDualCamera(width1=640, height1=480, width2=1280, height2=720)

    try:
        dual_camera.initialize()

        # Capturar frames de teste
        print("\n📷 Capturando frames de teste...")
        frame1, frame2 = dual_camera.capture_frames()

        if frame1 is not None:
            print("✅ Câmera 1: Frame capturado com sucesso")
        else:
            print("❌ Câmera 1: Falha na captura")

        if frame2 is not None:
            print("✅ Câmera 2: Frame capturado com sucesso")
        else:
            print("❌ Câmera 2: Falha na captura")

        # Teste estéreo
        print("\n🎯 Testando modo estéreo...")
        stereo1, stereo2 = dual_camera.capture_stereo()

        if stereo1 is not None and stereo2 is not None:
            print("✅ Sistema estéreo: OK")
        else:
            print("⚠️ Sistema estéreo: Incompleto")

        print("\n🎉 Teste concluído!")

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")

    finally:
        dual_camera.release()

if __name__ == "__main__":
    main()