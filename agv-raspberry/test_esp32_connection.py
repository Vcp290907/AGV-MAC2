#!/usr/bin/env python3
"""
Script de teste para comunicação com ESP32
Testa conexão serial e comandos básicos
"""

import sys
import time
from esp32_control import ESP32Controller, connect_esp32

def test_basic_connection():
    """Testa conexão básica com ESP32"""
    print("🧪 Testando conexão básica com ESP32...")

    controller = ESP32Controller()

    if controller.connect():
        print("✅ Conectado ao ESP32!")

        # Teste ping
        print("📡 Testando ping...")
        status = controller.get_status()
        if status['success']:
            print("✅ Ping OK!")
            print(f"   Status: {status['status']}")
        else:
            print("❌ Ping falhou!")
            return False

        controller.disconnect()
        return True
    else:
        print("❌ Falha na conexão!")
        return False

def test_motor_commands():
    """Testa comandos de movimento"""
    print("\n🚗 Testando comandos de movimento...")

    controller = ESP32Controller()

    if not controller.connect():
        print("❌ Não foi possível conectar ao ESP32")
        return False

    try:
        # Teste movimento para frente
        print("   Testando movimento para frente (0.5s)...")
        result = controller.move_forward(0.5)
        print(f"   Resultado: {result}")

        time.sleep(1)  # Pausa

        # Teste movimento para trás
        print("   Testando movimento para trás (0.5s)...")
        result = controller.move_backward(0.5)
        print(f"   Resultado: {result}")

        time.sleep(1)  # Pausa

        # Teste parada
        print("   Testando parada...")
        result = controller.stop()
        print(f"   Resultado: {result}")

        print("✅ Todos os testes de movimento concluídos!")
        return True

    except Exception as e:
        print(f"❌ Erro durante testes: {e}")
        return False

    finally:
        controller.disconnect()

def test_speed_control():
    """Testa controle de velocidade"""
    print("\n⚙️ Testando controle de velocidade...")

    controller = ESP32Controller()

    if not controller.connect():
        print("❌ Não foi possível conectar ao ESP32")
        return False

    try:
        # Testar diferentes velocidades
        speeds = [128, 192, 255]  # 50%, 75%, 100%

        for speed in speeds:
            print(f"   Testando velocidade {speed}...")
            result = controller.set_speed(speed)
            print(f"   Resultado: {result}")

            # Movimento curto para testar
            result = controller.move_forward(0.3)
            print(f"   Movimento: {result}")

            time.sleep(0.5)

        print("✅ Teste de velocidade concluído!")
        return True

    except Exception as e:
        print(f"❌ Erro no teste de velocidade: {e}")
        return False

    finally:
        controller.disconnect()

def interactive_test():
    """Teste interativo"""
    print("\n🎮 MODO INTERATIVO")
    print("==================")
    print("Comandos disponíveis:")
    print("  f - Mover para frente (1s)")
    print("  b - Mover para trás (1s)")
    print("  s - Parar")
    print("  1-9 - Velocidade (1=slow, 9=fast)")
    print("  t - Teste de status")
    print("  q - Sair")
    print()

    controller = ESP32Controller()

    if not controller.connect():
        print("❌ Não foi possível conectar ao ESP32")
        return

    try:
        while True:
            cmd = input("Comando: ").strip().lower()

            if cmd == 'q':
                break
            elif cmd == 'f':
                print("🚗 Movendo para frente...")
                result = controller.move_forward(1.0)
                print(f"Resultado: {result}")
            elif cmd == 'b':
                print("🚗 Movendo para trás...")
                result = controller.move_backward(1.0)
                print(f"Resultado: {result}")
            elif cmd == 's':
                print("🛑 Parando...")
                result = controller.stop()
                print(f"Resultado: {result}")
            elif cmd == 't':
                print("📊 Obtendo status...")
                result = controller.get_status()
                print(f"Status: {result}")
            elif cmd in '123456789':
                speed = int(cmd) * 28  # 28, 56, 84, ..., 252
                print(f"⚙️ Definindo velocidade para {speed}...")
                result = controller.set_speed(speed)
                print(f"Resultado: {result}")
            else:
                print("❌ Comando inválido!")

    except KeyboardInterrupt:
        print("\n🛑 Interrupção detectada")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        controller.disconnect()
        print("🔌 Desconectado")

def main():
    """Função principal"""
    print("🧪 TESTE DE COMUNICAÇÃO ESP32")
    print("=" * 40)

    if len(sys.argv) > 1:
        test_type = sys.argv[1]

        if test_type == "basic":
            success = test_basic_connection()
        elif test_type == "motors":
            success = test_motor_commands()
        elif test_type == "speed":
            success = test_speed_control()
        elif test_type == "interactive":
            interactive_test()
            return  # interactive_test() já cuida do encerramento
        else:
            print(f"❌ Tipo de teste inválido: {test_type}")
            print("Uso: python test_esp32_connection.py [basic|motors|speed|interactive]")
            return
    else:
        # Executar todos os testes
        print("Executando todos os testes...\n")

        success = True
        success &= test_basic_connection()
        success &= test_motor_commands()
        success &= test_speed_control()

    print("\n" + "=" * 40)
    if success:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("🎉 ESP32 está funcionando corretamente!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique a conexão e configuração do ESP32")

if __name__ == "__main__":
    main()