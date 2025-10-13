#!/usr/bin/env python3
"""
Teste básico da câmera Picamera2
"""

from picamera2 import Picamera2
import time

print("🔍 TESTANDO PICAMERA2...")

try:
    # Verificar câmeras disponíveis
    cameras = Picamera2.global_camera_info()
    print(f"📷 Câmeras encontradas: {len(cameras)}")
    for i, cam in enumerate(cameras):
        print(f"  {i}: {cam}")

    if not cameras:
        print("❌ Nenhuma câmera encontrada!")
        exit(1)

    # Tentar inicializar câmera
    print("\n📷 Inicializando câmera...")
    picam2 = Picamera2()

    # Configuração simples
    config = picam2.create_preview_configuration(
        main={"format": 'RGB888', "size": (640, 480)}
    )
    print("✅ Configuração criada")

    picam2.configure(config)
    print("✅ Câmera configurada")

    picam2.start()
    print("✅ Câmera iniciada")

    # Aguardar um pouco
    time.sleep(1)

    # Tentar capturar
    print("📸 Capturando frame...")
    frame = picam2.capture_array()
    print(f"✅ Frame capturado: {frame.shape if frame is not None else 'None'}")

    # Parar câmera
    picam2.stop()
    print("🛑 Câmera parada")

    print("✅ TESTE CONCLUÍDO COM SUCESSO!")

except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()