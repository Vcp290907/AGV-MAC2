#!/usr/bin/env python3
"""
Teste específico do Raspberry Pi para o sistema QR codes
Executa apenas no Raspberry Pi com câmera CSI
"""

import sys
import os
import platform

def verificar_raspberry_pi():
    """Verifica se estamos executando no Raspberry Pi"""
    sistema = platform.system().lower()
    arquitetura = platform.machine().lower()

    if sistema == "linux" and ("arm" in arquitetura or "aarch64" in arquitetura):
        return True
    else:
        print("❌ Este teste é específico para Raspberry Pi")
        print(f"🔍 Detectado: {sistema} {arquitetura}")
        return False

def testar_camera_raspberry():
    """Testa especificamente os módulos de câmera do Raspberry Pi"""
    print("📷 Testando módulos de câmera do Raspberry Pi...")

    modulos_camera = [
        ('picamera2', 'Picamera2'),
        ('libcamera', 'libcamera')
    ]

    sucesso = 0

    for modulo, nome in modulos_camera:
        try:
            if modulo == 'picamera2':
                import picamera2
                print(f"✅ {nome} importado com sucesso")
                sucesso += 1
            elif modulo == 'libcamera':
                import libcamera
                print(f"✅ {nome} importado com sucesso")
                sucesso += 1

        except ImportError as e:
            print(f"❌ {nome} não encontrado: {e}")
        except Exception as e:
            print(f"❌ Erro ao importar {nome}: {e}")

    return sucesso

def testar_qr_com_camera():
    """Testa o sistema QR codes com câmera real"""
    print("\n📱 Testando sistema QR codes com câmera...")

    try:
        from qr_code_reader import QRCodeReader

        # Criar reader com câmera real
        reader = QRCodeReader(camera_id=0, usar_camera=True)

        print("✅ QRCodeReader criado com câmera real")

        # Tentar capturar um frame de teste
        try:
            frame = reader.capturar_frame_teste()
            if frame is not None:
                print("✅ Frame de teste capturado com sucesso")
                print(f"📐 Resolução: {frame.shape[1]}x{frame.shape[0]}")

                # Tentar detectar QR codes no frame
                qr_codes = reader.detectar_qr_codes(frame)
                print(f"📊 QR codes detectados no teste: {len(qr_codes)}")

                return True
            else:
                print("⚠️ Não foi possível capturar frame de teste")
                return False

        except Exception as e:
            print(f"❌ Erro ao testar câmera: {e}")
            return False

    except Exception as e:
        print(f"❌ Erro ao criar QRCodeReader: {e}")
        return False

def main():
    """Função principal do teste Raspberry Pi"""
    print("🚀 TESTE ESPECÍFICO RASPBERRY PI - Sistema QR codes")
    print("=" * 60)

    if not verificar_raspberry_pi():
        sys.exit(1)

    # Verificar se estamos no diretório correto
    if not os.path.exists('qr_code_reader.py'):
        print("❌ Arquivo qr_code_reader.py não encontrado!")
        print("📂 Execute este script do diretório agv-raspberry/")
        sys.exit(1)

    # Executar testes
    teste1 = testar_camera_raspberry()
    teste2 = testar_qr_com_camera()

    print("\n" + "=" * 60)

    if teste1 > 0:
        print(f"🎉 Módulos de câmera OK ({teste1}/2)")
    else:
        print("💥 Módulos de câmera falharam")

    if teste2:
        print("🎉 Sistema QR codes com câmera OK")
    else:
        print("💥 Sistema QR codes com câmera falhou")

    if teste1 > 0 and teste2:
        print("\n🎊 SISTEMA COMPLETO FUNCIONANDO NO RASPBERRY PI!")
        return 0
    else:
        print("\n⚠️ Sistema parcialmente funcional. Verifique configurações.")
        return 1

if __name__ == "__main__":
    sys.exit(main())