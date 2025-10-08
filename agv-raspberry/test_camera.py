#!/usr/bin/env python3
"""
Script para testar câmeras no Raspberry Pi 5
Testa diferentes tipos de câmeras: USB, CSI, IP
"""

import cv2
import numpy as np
import time
import sys
import subprocess
import platform
import os

def check_system_info():
    """Verifica informações do sistema"""
    print("🔍 VERIFICANDO SISTEMA")
    print("=" * 50)

    print(f"📋 Sistema: {platform.system()}")
    print(f"🔧 Versão: {platform.release()}")
    print(f"💻 Arquitetura: {platform.machine()}")

    # Verificar se está no Raspberry Pi
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip()
            print(f"🖥️  Modelo: {model}")
    except:
        print("⚠️  Não foi possível identificar o modelo")

    print()

def check_camera_hardware():
    """Verifica hardware de câmera disponível"""
    print("📷 VERIFICANDO HARDWARE DE CÂMERA")
    print("=" * 50)

    # Verificar dispositivos USB (webcams)
    print("🔌 Dispositivos USB conectados:")
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
        usb_devices = result.stdout.split('\n')
        camera_devices = [d for d in usb_devices if 'camera' in d.lower() or 'webcam' in d.lower() or 'video' in d.lower()]
        if camera_devices:
            for device in camera_devices:
                print(f"   ✅ {device}")
        else:
            print("   ❌ Nenhum dispositivo de câmera USB encontrado")
    except:
        print("   ❌ Erro ao verificar dispositivos USB")

    # Verificar câmera CSI (Raspberry Pi Camera)
    print("\n📹 Verificando câmera CSI:")
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True, timeout=5)
        if 'detected=1' in result.stdout:
            print("   ✅ Câmera CSI detectada")
        else:
            print("   ❌ Câmera CSI não detectada")
    except:
        print("   ❌ Erro ao verificar câmera CSI (vcgencmd não encontrado)")

    print()

def test_opencv_installation():
    """Testa se OpenCV está instalado corretamente"""
    print("🐍 TESTANDO OPENCV")
    print("=" * 50)

    try:
        print(f"📦 OpenCV versão: {cv2.__version__}")
        print("✅ OpenCV importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar OpenCV: {e}")
        print("💡 Instale com: pip install opencv-python opencv-contrib-python")
        return False

    # Testar funcionalidades básicas
    try:
        # Criar imagem de teste
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = [255, 0, 0]  # Azul

        # Testar conversão de cor
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("✅ Funcionalidades básicas do OpenCV OK")
    except Exception as e:
        print(f"❌ Erro nas funcionalidades do OpenCV: {e}")
        return False

    print()
    return True

def test_camera_index(index, name):
    """Testa uma câmera específica por índice"""
    print(f"📷 Testando {name} (índice {index})...")

    cap = None
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print(f"   ❌ Não foi possível abrir {name}")
            return False

        # Obter propriedades da câmera
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"   ✅ {name} aberta com sucesso")
        print(f"      📐 Resolução: {width}x{height}")
        print(f"      🎬 FPS: {fps}")

        # Capturar alguns frames para teste
        print("      📸 Testando captura de frames...")
        for i in range(3):
            ret, frame = cap.read()
            if ret:
                print(f"         ✅ Frame {i+1} capturado")
            else:
                print(f"         ❌ Erro ao capturar frame {i+1}")
                return False
            time.sleep(0.1)

        print(f"   ✅ {name} funcionando corretamente!")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao testar {name}: {e}")
        return False
    finally:
        if cap:
            cap.release()

def test_usb_cameras():
    """Testa câmeras USB (webcams)"""
    print("🔌 TESTANDO CÂMERAS USB")
    print("=" * 50)

    success_count = 0
    max_cameras = 5  # Testar até 5 índices

    for i in range(max_cameras):
        if test_camera_index(i, f"Câmera USB {i}"):
            success_count += 1

    if success_count == 0:
        print("❌ Nenhuma câmera USB encontrada ou funcionando")
    else:
        print(f"✅ {success_count} câmera(s) USB funcionando")

    print()
    return success_count > 0

def test_csi_camera():
    """Testa câmera CSI do Raspberry Pi"""
    print("📹 TESTANDO CÂMERA CSI")
    print("=" * 50)

    # No Raspberry Pi 5, a câmera CSI pode aparecer como /dev/video0 ou outro índice
    # Vamos testar índices comuns
    csi_indices = [0, 1, 2, 10, 11, 12]  # Índices comuns para CSI

    success = False
    for idx in csi_indices:
        if test_camera_index(idx, f"Câmera CSI (video{idx})"):
            success = True
            break

    if not success:
        print("❌ Câmera CSI não encontrada ou não funcionando")
        print("💡 Possíveis soluções:")
        print("   1. Verifique se a câmera está conectada")
        print("   2. Execute: sudo raspi-config -> Interfacing Options -> Camera")
        print("   3. Reinicie o Raspberry Pi")
        print("   4. Teste: vcgencmd get_camera")

    print()
    return success

def test_ip_camera():
    """Testa câmera IP (se disponível)"""
    print("🌐 TESTANDO CÂMERA IP")
    print("=" * 50)

    # URLs comuns de teste para câmeras IP
    test_urls = [
        "rtsp://192.168.1.100:554/live",
        "http://192.168.1.100:8080/video",
        "rtsp://admin:admin@192.168.1.100:554/stream"
    ]

    print("🔍 Procurando câmeras IP na rede local...")
    print("⚠️  Este teste pode levar alguns segundos")

    success = False
    for url in test_urls:
        print(f"   Testando: {url}")
        try:
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"   ✅ Câmera IP encontrada: {width}x{height}")
                    success = True
                    cap.release()
                    break
            cap.release()
        except:
            pass

    if not success:
        print("❌ Nenhuma câmera IP encontrada nos URLs de teste")
        print("💡 Para testar uma câmera IP específica, use:")
        print("   cv2.VideoCapture('rtsp://user:pass@ip:port/stream')")

    print()
    return success

def create_test_image():
    """Cria uma imagem de teste para verificar display"""
    print("🖼️  CRIANDO IMAGEM DE TESTE")
    print("=" * 50)

    try:
        # Criar imagem colorida
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = [0, 255, 0]  # Verde

        # Adicionar texto
        cv2.putText(img, "TESTE CAMERA AGV", (50, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

        # Salvar imagem
        cv2.imwrite('teste_camera.jpg', img)
        print("✅ Imagem de teste criada: teste_camera.jpg")

        # Tentar exibir (se display disponível)
        try:
            cv2.imshow('Teste Camera', img)
            print("✅ Janela de exibição aberta (pressione qualquer tecla para fechar)")
            cv2.waitKey(3000)  # 3 segundos
            cv2.destroyAllWindows()
        except:
            print("⚠️  Display não disponível (normal em SSH)")

    except Exception as e:
        print(f"❌ Erro ao criar imagem de teste: {e}")

    print()

def main():
    """Função principal"""
    print("🚀 TESTE DE CÂMERAS - SISTEMA AGV RASPBERRY PI 5")
    print("=" * 60)
    print()

    # Verificações básicas
    check_system_info()
    check_camera_hardware()

    # Testar OpenCV
    if not test_opencv_installation():
        print("❌ OpenCV não está funcionando. Instale com:")
        print("   pip install opencv-python opencv-contrib-python")
        sys.exit(1)

    # Testar câmeras
    usb_ok = test_usb_cameras()
    csi_ok = test_csi_camera()
    ip_ok = test_ip_camera()

    # Criar imagem de teste
    create_test_image()

    # Resumo final
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    print(f"USB Cameras: {'✅ OK' if usb_ok else '❌ FALHA'}")
    print(f"CSI Camera:  {'✅ OK' if csi_ok else '❌ FALHA'}")
    print(f"IP Cameras:  {'✅ OK' if ip_ok else '❌ FALHA'}")

    total_ok = sum([usb_ok, csi_ok, ip_ok])
    if total_ok > 0:
        print(f"\n🎉 {total_ok} tipo(s) de câmera funcionando!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Configure a câmera no seu código principal")
        print("   2. Teste captura de QR codes")
        print("   3. Implemente detecção de obstáculos")
    else:
        print("\n❌ Nenhuma câmera funcionando")
        print("\n🔧 SOLUÇÕES:")
        print("   1. Conecte uma webcam USB")
        print("   2. Configure câmera CSI: sudo raspi-config")
        print("   3. Verifique conexões e drivers")
        print("   4. Teste: ls /dev/video*")

if __name__ == "__main__":
    main()