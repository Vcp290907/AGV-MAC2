#!/usr/bin/env python3
"""
Teste básico do sistema de QR codes do AGV
Verifica se os módulos podem ser importados corretamente
"""

import sys
import os
import platform

def detectar_ambiente():
    """Detecta se estamos no Raspberry Pi ou PC"""
    sistema = platform.system().lower()
    arquitetura = platform.machine().lower()

    if sistema == "linux" and ("arm" in arquitetura or "aarch64" in arquitetura):
        return "raspberry_pi"
    else:
        return "pc_windows"

def testar_imports():
    """Testa se todos os módulos necessários podem ser importados"""
    ambiente = detectar_ambiente()
    print(f"🧪 Testando imports do sistema QR codes ({ambiente})...")

    modulos_obrigatorios = []
    modulos_opcionais_rpi = []

    # Módulos sempre necessários
    modulos_obrigatorios.extend([
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('pyzbar', 'pyzbar')
    ])

    # Módulos específicos do Raspberry Pi
    if ambiente == "raspberry_pi":
        modulos_opcionais_rpi.extend([
            ('picamera2', 'Picamera2'),
            ('libcamera', 'libcamera')
        ])

    sucesso_obrigatorios = 0
    sucesso_opcionais = 0

    # Testar módulos obrigatórios
    for modulo, nome in modulos_obrigatorios:
        try:
            if modulo == 'cv2':
                import cv2
                print(f"✅ {nome} {cv2.__version__} importado com sucesso")
            elif modulo == 'numpy':
                import numpy as np
                print(f"✅ {nome} {np.__version__} importado com sucesso")
            elif modulo == 'PIL':
                from PIL import Image
                print(f"✅ {nome} importado com sucesso")
            elif modulo == 'pyzbar':
                import pyzbar
                print(f"✅ {nome} importado com sucesso")

            sucesso_obrigatorios += 1

        except ImportError as e:
            print(f"❌ {nome} não encontrado: {e}")
        except Exception as e:
            print(f"❌ Erro ao importar {nome}: {e}")

    # Testar módulos opcionais do Raspberry Pi
    for modulo, nome in modulos_opcionais_rpi:
        try:
            if modulo == 'picamera2':
                import picamera2
                print(f"✅ {nome} importado com sucesso")
            elif modulo == 'libcamera':
                import libcamera
                print(f"✅ {nome} importado com sucesso")

            sucesso_opcionais += 1

        except ImportError:
            print(f"⚠️  {nome} não disponível (normal no PC)")
        except Exception as e:
            print(f"❌ Erro ao importar {nome}: {e}")

    total_obrigatorios = len(modulos_obrigatorios)
    total_opcionais = len(modulos_opcionais_rpi)

    print(f"\n📊 Resultado: {sucesso_obrigatorios}/{total_obrigatorios} módulos obrigatórios OK")

    if ambiente == "raspberry_pi":
        print(f"📊 Módulos Raspberry Pi: {sucesso_opcionais}/{total_opcionais} OK")
    else:
        print(f"📊 Ambiente PC: OK para desenvolvimento")

    return sucesso_obrigatorios == total_obrigatorios

def testar_classe_qr():
    """Testa a criação da classe QRCodeReader"""
    print("\n🧪 Testando classe QRCodeReader...")

    try:
        import sys
        import platform

        if platform.system() != "Linux":
            # No Windows, criar uma classe mock para AGVCamera
            class MockAGVCamera:
                def __init__(self, camera_id=0, width=640, height=480):
                    self.camera_id = camera_id
                    self.width = width
                    self.height = height
                    self.initialized = False

                def initialize(self):
                    self.initialized = True
                    return True

                def capture_frame(self):
                    # Retornar uma imagem dummy
                    return np.zeros((480, 640, 3), dtype=np.uint8)

                def release(self):
                    pass

            # Temporariamente substituir o import
            sys.modules['agv_camera'] = type('MockModule', (), {'AGVCamera': MockAGVCamera})()

        from qr_code_reader import QRCodeReader

        # Criar instância (sem câmera para teste)
        reader = QRCodeReader(camera_id=0)
        print("✅ Classe QRCodeReader criada com sucesso")

        # Testar métodos principais
        if hasattr(reader, 'detectar_qr_codes'):
            print("✅ Método detectar_qr_codes encontrado")
        else:
            print("❌ Método detectar_qr_codes não encontrado")
            return False

        if hasattr(reader, 'desenhar_qr_codes'):
            print("✅ Método desenhar_qr_codes encontrado")
        else:
            print("❌ Método desenhar_qr_codes não encontrado")
            return False

        return True

    except Exception as e:
        print(f"❌ Erro ao testar classe: {e}")
        return False

def main():
    """Função principal do teste"""
    print("🚀 Iniciando teste do sistema QR codes do AGV")
    print("=" * 50)

    # Verificar se estamos no diretório correto
    if not os.path.exists('qr_code_reader.py'):
        print("❌ Arquivo qr_code_reader.py não encontrado!")
        print("📂 Execute este script do diretório agv-raspberry/")
        sys.exit(1)

    # Executar testes
    teste1 = testar_imports()
    teste2 = testar_classe_qr()

    print("\n" + "=" * 50)
    if teste1 and teste2:
        print("🎉 Todos os testes passaram! Sistema QR codes OK.")
        return 0
    else:
        print("💥 Alguns testes falharam. Verifique as dependências.")
        return 1

if __name__ == "__main__":
    sys.exit(main())