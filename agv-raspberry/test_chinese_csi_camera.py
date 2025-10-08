#!/usr/bin/env python3
"""
Script específico para testar câmeras CSI chinesas no Raspberry Pi 5
Câmeras chinesas geralmente não funcionam com libcamera, usam V4L2 diretamente
"""

import cv2
import numpy as np
import time
import subprocess
import sys
import os

def check_v4l2_devices():
    """Verifica dispositivos V4L2 disponíveis"""
    print("🔍 Verificando dispositivos V4L2...")
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'],
                              capture_output=True, text=True, timeout=5)
        print("Dispositivos encontrados:")
        print(result.stdout)
        return result.returncode == 0
    except:
        print("❌ v4l2-ctl não encontrado")
        return False

def test_chinese_csi_opencv():
    """Testa câmera CSI chinesa com OpenCV (V4L2 direto)"""
    print("\n🐍 Testando câmera CSI chinesa com OpenCV...")

    # Câmeras chinesas geralmente aparecem em índices baixos
    test_indices = [0, 1, 2, 3, 4]

    for index in test_indices:
        print(f"   Testando índice {index}...")

        try:
            # Tentar abrir com V4L2
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)

            if cap.isOpened():
                # Configurar parâmetros comuns para câmeras chinesas
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)

                # Tentar ler alguns frames
                for attempt in range(3):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"   ✅ Câmera chinesa funcionando (índice {index})")
                        print(f"      📐 Resolução: {width}x{height}")

                        # Salvar frame de teste
                        cv2.imwrite('teste_chinese_csi.jpg', frame)
                        print("      💾 Frame salvo: teste_chinese_csi.jpg")

                        # Verificar se imagem foi salva
                        if os.path.exists('teste_chinese_csi.jpg'):
                            file_size = os.path.getsize('teste_chinese_csi.jpg')
                            print(f"      📁 Tamanho do arquivo: {file_size} bytes")

                        cap.release()
                        return True

                    time.sleep(0.5)  # Pequena pausa entre tentativas

                cap.release()
            else:
                print(f"   ❌ Índice {index} não abriu")

        except Exception as e:
            print(f"   ❌ Erro no índice {index}: {e}")

    print("❌ Não foi possível acessar câmera CSI chinesa")
    return False

def test_chinese_csi_formats():
    """Testa diferentes formatos de câmera chinesa"""
    print("\n📹 Testando formatos de câmera chinesa...")

    try:
        # Verificar formatos suportados
        result = subprocess.run(['v4l2-ctl', '--list-formats-ext', '-d', '/dev/video0'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("Formatos suportados por /dev/video0:")
            print(result.stdout)
        else:
            print("❌ Erro ao listar formatos")

    except Exception as e:
        print(f"❌ Erro ao verificar formatos: {e}")

def test_chinese_csi_v4l2():
    """Testa câmera chinesa usando v4l2 diretamente"""
    print("\n📷 Testando câmera chinesa com v4l2-ctl...")

    try:
        # Tentar capturar uma imagem com v4l2-ctl
        result = subprocess.run([
            'v4l2-ctl', '--device=/dev/video0',
            '--set-fmt-video=width=640,height=480,pixelformat=YUYV',
            '--stream-mmap', '--stream-count=1',
            '--stream-to=teste_v4l2.raw'
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print("✅ v4l2-ctl conseguiu acessar câmera")
            if os.path.exists('teste_v4l2.raw'):
                file_size = os.path.getsize('teste_v4l2.raw')
                print(f"   📁 Dados brutos salvos: {file_size} bytes")
            return True
        else:
            print(f"❌ Erro no v4l2-ctl: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Erro ao executar v4l2-ctl: {e}")
        return False

def test_chinese_csi_gstreamer():
    """Testa câmera chinesa com GStreamer (sem libcamerasrc)"""
    print("\n🎬 Testando câmera chinesa com GStreamer...")

    # Pipeline GStreamer para câmeras V4L2 genéricas
    pipelines = [
        "v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480 ! videoconvert ! video/x-raw,format=BGR ! appsink",
        "v4l2src device=/dev/video0 ! image/jpeg,width=640,height=480 ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink"
    ]

    for i, pipeline in enumerate(pipelines):
        print(f"   Testando pipeline {i+1}: {pipeline[:60]}...")

        try:
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print("✅ GStreamer pipeline funcionando!")
                    print(f"   📐 Resolução: {width}x{height}")

                    cv2.imwrite('teste_chinese_gstreamer.jpg', frame)
                    print("   💾 Frame salvo: teste_chinese_gstreamer.jpg")

                    cap.release()
                    return True

            cap.release()
        except Exception as e:
            print(f"❌ Erro no pipeline {i+1}: {e}")

    print("❌ Todos os pipelines GStreamer falharam")
    return False

def create_chinese_csi_test_script():
    """Cria script de teste contínuo para câmera CSI chinesa"""
    script_content = '''#!/usr/bin/env python3
"""
Script de teste contínuo para câmera CSI chinesa
Execute: python test_chinese_csi_continuous.py
Pare com Ctrl+C
"""

import cv2
import numpy as np
import time
import signal
import sys

def signal_handler(sig, frame):
    print("\\n🛑 Teste interrompido pelo usuário")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("🎥 TESTE CONTÍNUO - CÂMERA CSI CHINESA")
    print("=====================================")
    print("Pressione Ctrl+C para parar")

    # Tentar diferentes índices
    camera_index = None
    for idx in [0, 1, 2]:
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            camera_index = idx
            cap.release()
            break

    if camera_index is None:
        print("❌ Nenhuma câmera encontrada")
        return

    print(f"📷 Usando câmera no índice {camera_index}")

    cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if ret:
                frame_count += 1

                # Mostrar informações a cada 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    height, width = frame.shape[:2]
                    print(f"📊 Frame {frame_count}: {width}x{height} | FPS: {fps:.1f}")

                # Mostrar preview (opcional - remover se sem display)
                cv2.imshow('CSI Chinesa - Preview', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            else:
                print("❌ Erro ao capturar frame")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\\n🛑 Teste interrompido")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"\\n📈 Estatísticas finais:")
        print(f"   Frames capturados: {frame_count}")
        print(f"   Tempo total: {elapsed:.1f}s")
        print(f"   FPS médio: {avg_fps:.1f}")

if __name__ == "__main__":
    main()
'''

    try:
        with open('test_chinese_csi_continuous.py', 'w') as f:
            f.write(script_content)
        os.chmod('test_chinese_csi_continuous.py', 0o755)
        print("✅ Script de teste contínuo criado: test_chinese_csi_continuous.py")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        return False

def main():
    """Função principal"""
    print("🎥 TESTE ESPECÍFICO - CÂMERA CSI CHINESA")
    print("=======================================")
    print("Câmeras chinesas não funcionam com libcamera")
    print("Usam V4L2 diretamente (/dev/video0, /dev/video1, etc.)")
    print()

    # Verificar dispositivos
    check_v4l2_devices()

    # Executar testes
    results = {}

    # Teste principal com OpenCV
    results['opencv'] = test_chinese_csi_opencv()

    # Teste com v4l2-ctl
    results['v4l2'] = test_chinese_csi_v4l2()

    # Teste com GStreamer
    results['gstreamer'] = test_chinese_csi_gstreamer()

    # Verificar formatos
    test_chinese_csi_formats()

    # Criar script de teste contínuo
    results['script'] = create_chinese_csi_test_script()

    # Resumo
    print("\n📊 RESUMO DOS TESTES - CSI CHINESA")
    print("OpenCV (V4L2):     ", "✅ OK" if results.get('opencv') else "❌ FALHA")
    print("v4l2-ctl:          ", "✅ OK" if results.get('v4l2') else "❌ FALHA")
    print("GStreamer:         ", "✅ OK" if results.get('gstreamer') else "❌ FALHA")
    print("Script criado:     ", "✅ OK" if results.get('script') else "❌ FALHA")

    # Verificar se pelo menos um teste passou
    if any(results.values()):
        print("\n🎉 Pelo menos um método funcionou!")
        print("💡 Use o método que funcionou no seu código principal")
    else:
        print("\n❌ Todos os testes falharam")
        print("💡 Verifique:")
        print("   - Conexão física do cabo CSI")
        print("   - Alimentação da câmera (5V)")
        print("   - Drivers V4L2 instalados")
        print("   - Câmera compatível com Raspberry Pi")

if __name__ == "__main__":
    main()