#!/usr/bin/env python3
"""
Script de teste para comunicação com ESP32
Testa conexão serial e comandos básicos
"""

import sys
import time
from esp32_control import ESP32Controller, connect_esp32

def test_basic_connection(port=None):
    """Testa conexão básica com ESP32"""
    print("🧪 Testando conexão básica com ESP32...")

    controller = ESP32Controller(port=port)

    if controller.connect():
        print("✅ Conectado ao ESP32!")
        print(f"   Porta: {controller.port}")

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

def test_motor_commands(port=None):
    """Testa comandos de movimento"""
    print("\n🚗 Testando comandos de movimento...")

    controller = ESP32Controller(port=port)

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

def test_speed_control(port=None):
    """Testa controle de velocidade (não disponível para servo motores)"""
    print("\n⚙️ Testando controle de velocidade...")

    controller = ESP32Controller(port=port)

    if not controller.connect():
        print("❌ Não foi possível conectar ao ESP32")
        return False

    try:
        print("   ℹ️  Servo motores não têm controle de velocidade variável")
        print("   ℹ️  Testando comando set_speed (deve retornar mensagem informativa)...")

        result = controller.set_speed(128)
        print(f"   Resultado: {result}")

        if result.get('message') and 'não disponível' in result['message'].lower():
            print("✅ Comportamento correto - velocidade não suportada")
            return True
        else:
            print("⚠️  Resposta inesperada")
            return False

    except Exception as e:
        print(f"❌ Erro no teste de velocidade: {e}")
        return False

    finally:
        controller.disconnect()

def interactive_test(port=None):
    """Teste interativo"""
    print("\n🎮 MODO INTERATIVO")
    print("==================")
    print("Comandos disponíveis:")
    print("  f - Mover para frente (1s)")
    print("  b - Mover para trás (1s)")
    print("  s - Parar")
    print("  t - Teste de status")
    print("  q - Sair")
    print()

    controller = ESP32Controller(port=port)

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
                print("⚠️  Controle de velocidade não disponível para servo motores")
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

    # Parse argumentos
    port = None
    test_type = None

    if not port:
        # Tentar ler do arquivo esp32_port.txt
        try:
            with open('esp32_port.txt', 'r') as f:
                file_content = f.read().strip()
                # Limpar conteúdo (remover caracteres estranhos)
                port = file_content.split('/dev/tty')[1]  # Pega apenas a parte após /dev/tty
                port = f'/dev/tty{port.split()[0]}'  # Remove qualquer coisa após espaço
                print(f"📁 Porta lida do arquivo: {port}")
        except (FileNotFoundError, IndexError):
            print("🔍 Arquivo esp32_port.txt não encontrado ou inválido, usando auto-detecção")
            port = None
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = args[i + 1]
            i += 2
        else:
            if not test_type:
                test_type = args[i]
            i += 1

    if port:
        print(f"📍 Usando porta especificada: {port}")
    else:
        print("🔍 Usando auto-detecção de porta")

    if test_type:
        if test_type == "basic":
            success = test_basic_connection(port)
        elif test_type == "motors":
            success = test_motor_commands(port)
        elif test_type == "speed":
            success = test_speed_control(port)
        elif test_type == "interactive":
            interactive_test(port)
            return  # interactive_test() já cuida do encerramento
        else:
            print(f"❌ Tipo de teste inválido: {test_type}")
            print("Uso: python test_esp32_connection.py [basic|motors|speed|interactive] [--port PORTA]")
            return
    else:
        # Executar todos os testes
        print("Executando todos os testes...\n")

        success = True
        success &= test_basic_connection(port)
        success &= test_motor_commands(port)
        # Removido teste de velocidade pois servo não tem controle de velocidade

    print("\n" + "=" * 40)
    if success:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("🎉 ESP32 está funcionando corretamente!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique a conexão e configuração do ESP32")
        print("\n💡 Dicas de solução:")
        print("   1. Execute: python detect_esp32.py")
        print("   2. Verifique se ESP32 está conectado e ligado")
        print("   3. Certifique-se que o firmware foi carregado")
        print("   4. Verifique permissões: sudo usermod -a -G dialout $USER")

if __name__ == "__main__":
    main()