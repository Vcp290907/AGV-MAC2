#!/usr/bin/env python3
"""
Script específico para testar câmera CSI no Raspberry Pi 5
Usa libcamera ou OpenCV para testar a câmera oficial
"""

import cv2
import numpy as np
import time
import subprocess
import sys
import os

def check_libcamera():
    """Verifica se libcamera está disponível"""
    print("🔍 Verificando libcamera...")
    try:
        result = subprocess.run(['libcamera-hello', '--version'],
                              capture_output=True, text=True, timeout=5)
        print("✅ libcamera encontrado")
        return True
    except:
        print("❌ libcamera não encontrado")
        return False

def test_libcamera_preview():
    """Testa preview da câmera com libcamera"""
    print("\n📷 Testando preview com libcamera...")
    try:
        print("   Iniciando preview (5 segundos)...")
        # Executa preview por 5 segundos
        result = subprocess.run(['libcamera-hello', '-t', '5000'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ Preview da câmera CSI funcionou!")
            return True
        else:
            print(f"❌ Erro no preview: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro ao executar libcamera: {e}")
        return False

def test_libcamera_capture():
    """Testa captura de imagem com libcamera"""
    print("\n📸 Testando captura de imagem com libcamera...")
    try:
        filename = 'teste_csi.jpg'
        result = subprocess.run(['libcamera-jpeg', '-o', filename, '-t', '2000'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"✅ Imagem capturada: {filename} ({file_size} bytes)")
            return True
        else:
            print(f"❌ Erro na captura: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro ao capturar imagem: {e}")
        return False

def test_opencv_csi():
    """Testa câmera CSI com OpenCV"""
    print("\n🐍 Testando câmera CSI com OpenCV...")

    # No Raspberry Pi 5, tentar diferentes backends
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_GSTREAMER, "GStreamer"),
        (cv2.CAP_ANY, "ANY")
    ]

    for backend, name in backends:
        print(f"   Testando backend {name}...")

        for index in [0, 1, 2, 10, 11, 12]:
            try:
                cap = cv2.VideoCapture(index, backend)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"   ✅ CSI funcionando com {name} (índice {index})")
                        print(f"      📐 Resolução: {width}x{height}")

                        # Salvar frame de teste
                        cv2.imwrite('teste_opencv_csi.jpg', frame)
                        print("      💾 Frame salvo: teste_opencv_csi.jpg"

                        cap.release()
                        return True

                cap.release()
            except:
                pass

    print("❌ Não foi possível acessar câmera CSI com OpenCV")
    return False

def test_gstreamer_pipeline():
    """Testa pipeline GStreamer para câmera CSI"""
    print("\n🎬 Testando pipeline GStreamer...")

    # Pipeline GStreamer para Raspberry Pi Camera
    pipeline = (
        "libcamerasrc ! "
        "video/x-raw,width=640,height=480,framerate=30/1 ! "
        "videoconvert ! "
        "video/x-raw,format=BGR ! "
        "appsink"
    )

    print(f"   Pipeline: {pipeline}")

    try:
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print("✅ GStreamer pipeline funcionando!"                print(f"   📐 Resolução: {width}x{height}")

                cv2.imwrite('teste_gstreamer.jpg', frame)
                print("   💾 Frame salvo: teste_gstreamer.jpg"

                cap.release()
                return True

        cap.release()
    except Exception as e:
        print(f"❌ Erro no pipeline GStreamer: {e}")

    print("❌ Pipeline GStreamer falhou")
    return False

def create_csi_test_script():
    """Cria script de teste contínuo para câmera CSI"""
    script_content = '''#!/usr/bin/env python3
"""
Script de teste contínuo para câmera CSI
Execute: python test_csi_continuous.py
Pare com Ctrl+C
"""

import cv2
import numpy as np
import time
import signal
import sys

running = True

def signal_handler(sig, frame):
    global running
    print("\\n🛑 Parando teste...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("🚀 Teste contínuo da câmera CSI")
    print("Pressione Ctrl+C para parar")
    print()

    # Tentar diferentes configurações
    configs = [
        (0, cv2.CAP_V4L2, "CSI V4L2"),
        (0, cv2.CAP_GSTREAMER, "CSI GStreamer"),
        (10, cv2.CAP_V4L2, "CSI Alt V4L2"),
    ]

    cap = None
    config_atual = None

    for index, backend, name in configs:
        print(f"Testando {name}...")
        try:
            if backend == cv2.CAP_GSTREAMER:
                # Usar pipeline GStreamer
                pipeline = (
                    "libcamerasrc ! "
                    "video/x-raw,width=640,height=480,framerate=30/1 ! "
                    "videoconvert ! "
                    "video/x-raw,format=BGR ! "
                    "appsink"
                )
                cap = cv2.VideoCapture(pipeline, backend)
            else:
                cap = cv2.VideoCapture(index, backend)

            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    config_atual = (index, backend, name)
                    print(f"✅ {name} funcionando!")
                    break

            cap.release()
            cap = None
        except Exception as e:
            print(f"❌ Erro com {name}: {e}")

    if not cap or not cap.isOpened():
        print("❌ Nenhuma configuração funcionou")
        return

    index, backend, name = config_atual
    print(f"\\n🎥 Usando: {name}")
    print("📊 Estatísticas:")

    frame_count = 0
    start_time = time.time()

    try:
        while running:
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_count += 1

                # Mostrar FPS a cada segundo
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    print(f"   FPS: {fps:.1f} | Frames: {frame_count} | Res: {frame.shape[1]}x{frame.shape[0]}")
                    frame_count = 0
                    start_time = time.time()

                # Adicionar timestamp na imagem
                timestamp = time.strftime("%H:%M:%S")
                cv2.putText(frame, timestamp, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Salvar frame a cada 10 segundos
                if int(time.time()) % 10 == 0:
                    filename = f"frame_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"   💾 Frame salvo: {filename}")

            else:
                print("❌ Erro ao capturar frame")
                time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("\\n👋 Teste finalizado")

if __name__ == "__main__":
    main()
'''

    with open('test_csi_continuous.py', 'w') as f:
        f.write(script_content)

    # Tornar executável
    os.chmod('test_csi_continuous.py', 0o755)

    print("✅ Script de teste contínuo criado: test_csi_continuous.py")
    print("   Execute: python test_csi_continuous.py")

def main():
    """Função principal"""
    print("🎥 TESTE ESPECÍFICO DE CÂMERA CSI - RASPBERRY PI 5")
    print("=" * 60)

    # Verificar libcamera
    libcamera_ok = check_libcamera()

    if libcamera_ok:
        # Testar com libcamera
        preview_ok = test_libcamera_preview()
        capture_ok = test_libcamera_capture()
    else:
        print("⚠️  libcamera não disponível, pulando testes específicos")
        preview_ok = capture_ok = False

    # Testar com OpenCV
    opencv_ok = test_opencv_csi()

    # Testar GStreamer
    gstreamer_ok = test_gstreamer_pipeline()

    # Criar script de teste contínuo
    create_csi_test_script()

    # Resumo
    print("\n📊 RESUMO DOS TESTES CSI")
    print("=" * 50)
    print(f"libcamera preview:  {'✅ OK' if preview_ok else '❌ FALHA'}")
    print(f"libcamera capture:  {'✅ OK' if capture_ok else '❌ FALHA'}")
    print(f"OpenCV CSI:         {'✅ OK' if opencv_ok else '❌ FALHA'}")
    print(f"GStreamer:          {'✅ OK' if gstreamer_ok else '❌ FALHA'}")

    working = sum([preview_ok, capture_ok, opencv_ok, gstreamer_ok])

    if working > 0:
        print(f"\n🎉 {working} método(s) funcionando!")
        print("\n💡 RECOMENDAÇÕES:")
        if opencv_ok:
            print("   ✅ Use OpenCV para integração com código Python")
        if gstreamer_ok:
            print("   ✅ GStreamer oferece melhor performance")
        if libcamera_ok:
            print("   ✅ libcamera para testes rápidos via terminal")

        print("\n🚀 Execute o teste contínuo:")
        print("   python test_csi_continuous.py")
    else:
        print("\n❌ Nenhum método funcionou")
        print("\n🔧 SOLUÇÕES PARA CSI:")
        print("   1. sudo raspi-config -> Interfacing Options -> Camera -> Enable")
        print("   2. sudo apt update && sudo apt install -y python3-libcamera python3-kms++")
        print("   3. sudo apt install -y gstreamer1.0-libcamera")
        print("   4. Reinicie o Raspberry Pi")
        print("   5. Verifique conexão da câmera")

if __name__ == "__main__":
    main()