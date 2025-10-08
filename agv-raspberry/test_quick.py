#!/usr/bin/env python3
"""
Teste ultra simples das câmeras AGV
"""

from agv_camera import AGVDualCamera

def main():
    print("🧪 TESTE ULTRA SIMPLES - CÂMERAS AGV")
    print("===================================")

    # Criar sistema dual
    camera = AGVDualCamera()

    try:
        # Inicializar
        camera.initialize()

        # Capturar uma vez
        frame1, frame2 = camera.capture_frames()

        # Resultado
        cam1_ok = frame1 is not None
        cam2_ok = frame2 is not None

        print("📊 RESULTADO:")
        print(f"Câmera 1: {'✅ OK' if cam1_ok else '❌ FALHA'}")
        print(f"Câmera 2: {'✅ OK' if cam2_ok else '❌ FALHA'}")

        if cam1_ok or cam2_ok:
            print("\n🎉 Pelo menos uma câmera funcionando!")
            print("Use: python3 agv_camera_live.py  # Para ver em tempo real")
        else:
            print("\n❌ Nenhuma câmera detectada")

    except Exception as e:
        print(f"❌ Erro: {e}")

    finally:
        camera.release()

if __name__ == "__main__":
    main()