#!/usr/bin/env python3
"""
Diagnóstico completo dos servo motores
Testa conexão, movimento e calibração
"""

import sys
import time
from esp32_control import ESP32Controller

def test_servo_connection():
    """Testa se o ESP32 está conectado e responde"""
    print("🔌 TESTANDO CONEXÃO COM ESP32...")

    controller = ESP32Controller()

    if not controller.connect():
        print("❌ Não foi possível conectar ao ESP32")
        print("💡 Verifique:")
        print("   - ESP32 conectado e ligado")
        print("   - Firmware carregado (esp32_motor_control.ino)")
        print("   - Porta USB correta")
        return False

    print("✅ ESP32 conectado com sucesso!")
    print(f"   Porta: {controller.port}")

    # Testar status
    status = controller.get_status()
    if status and status.get('success'):
        print("✅ Status OK!")
        data = status.get('data', {})
        print(f"   Motor type: {data.get('motor_type', 'unknown')}")
        print(f"   Motors enabled: {data.get('motors_enabled', 'unknown')}")
        print(f"   Uptime: {data.get('uptime_ms', 0)}ms")

        servos = data.get('servos', {})
        if servos:
            print("   📊 Status dos Servos:")
            print(f"      Esquerdo: {servos.get('left_angle', '?')}° (attached: {servos.get('left_attached', '?')})")
            print(f"      Direito: {servos.get('right_angle', '?')}° (attached: {servos.get('right_attached', '?')})")
        else:
            print("   ⚠️  Status dos servos não disponível")
    else:
        print("❌ Falha ao obter status")

    controller.disconnect()
    return True

def test_servo_movement():
    """Testa movimento básico dos servos"""
    print("\n🤖 TESTANDO MOVIMENTO DOS SERVOS...")

    controller = ESP32Controller()

    if not controller.connect():
        return False

    try:
        print("   🛑 1. Testando PARADA (posição neutra)...")
        result = controller.stop()
        print(f"   Resultado: {result}")
        time.sleep(2)

        print("   ⏩ 2. Testando FRENTE (1 segundo)...")
        result = controller.move_forward(1.0)
        print(f"   Resultado: {result}")
        time.sleep(2)

        print("   🛑 3. Parando novamente...")
        result = controller.stop()
        print(f"   Resultado: {result}")
        time.sleep(2)

        print("   ⏪ 4. Testando TRÁS (1 segundo)...")
        result = controller.move_backward(1.0)
        print(f"   Resultado: {result}")
        time.sleep(2)

        print("   🛑 5. Parada final...")
        result = controller.stop()
        print(f"   Resultado: {result}")

        print("✅ Teste de movimento concluído!")
        return True

    except Exception as e:
        print(f"❌ Erro durante teste de movimento: {e}")
        return False

    finally:
        controller.disconnect()

def interactive_servo_test():
    """Teste interativo para calibração manual"""
    print("\n🎛️  MODO INTERATIVO DE CALIBRAÇÃO")
    print("=" * 40)
    print("Comandos disponíveis:")
    print("  f - Mover para frente (1s)")
    print("  b - Mover para trás (1s)")
    print("  s - Parar")
    print("  l - Teste apenas servo esquerdo")
    print("  r - Teste apenas servo direito")
    print("  c - Calibração manual")
    print("  t - Status dos servos")
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
                print("⏩ Movendo para frente...")
                result = controller.move_forward(1.0)
                print(f"Resultado: {result}")
            elif cmd == 'b':
                print("⏪ Movendo para trás...")
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
            elif cmd == 'l':
                print("🧪 Teste manual - Servo esquerdo")
                _test_single_servo(controller, "left")
            elif cmd == 'r':
                print("🧪 Teste manual - Servo direito")
                _test_single_servo(controller, "right")
            elif cmd == 'c':
                print("🔧 Calibração manual...")
                manual_calibration(controller)
            else:
                print("❌ Comando inválido!")

    except KeyboardInterrupt:
        print("\n🛑 Interrupção detectada")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        controller.disconnect()
        print("🔌 Desconectado")

def _test_single_servo(controller, side):
    """Testa um servo individualmente"""
    try:
        # Este é um teste direto no ESP32 - vamos criar um comando customizado
        command = {
            'command': f'test_{side}_servo',
            'timestamp': time.time()
        }

        print(f"   Testando servo {side}...")
        response = controller._send_command(command)
        print(f"   Resposta: {response}")

    except Exception as e:
        print(f"   ❌ Erro no teste do servo {side}: {e}")

def manual_calibration(controller):
    """Calibração manual dos servos"""
    print("🔧 CALIBRAÇÃO MANUAL DOS SERVOS")
    print("Isso irá testar diferentes ângulos para encontrar a configuração correta")
    print()

    # Testar diferentes combinações
    test_configs = [
        {"name": "Frente Normal", "left": 0, "right": 180},
        {"name": "Frente Invertida", "left": 180, "right": 0},
        {"name": "Trás Normal", "left": 180, "right": 0},
        {"name": "Trás Invertida", "left": 0, "right": 180},
    ]

    for config in test_configs:
        print(f"🧪 Testando: {config['name']}")
        print(f"   Servo Esq: {config['left']}°, Servo Dir: {config['right']}°")

        # Enviar comando customizado para teste direto
        command = {
            'command': 'manual_test',
            'left_angle': config['left'],
            'right_angle': config['right'],
            'duration': 2.0,
            'timestamp': time.time()
        }

        response = controller._send_command(command)
        print(f"   Resposta: {response}")

        input("   Pressione ENTER para próximo teste...")

        # Parar
        controller.stop()
        time.sleep(1)

def main():
    """Função principal"""
    print("🔧 DIAGNÓSTICO COMPLETO DOS SERVO MOTORES")
    print("=" * 50)

    if len(sys.argv) > 1:
        test_type = sys.argv[1]

        if test_type == "connection":
            success = test_servo_connection()
        elif test_type == "movement":
            success = test_servo_movement()
        elif test_type == "interactive":
            interactive_servo_test()
            return
        else:
            print(f"❌ Tipo de teste inválido: {test_type}")
            print("Uso: python diagnose_servos.py [connection|movement|interactive]")
            return
    else:
        # Executar todos os testes
        print("Executando diagnóstico completo...\n")

        success = True
        success &= test_servo_connection()
        success &= test_servo_movement()

    print("\n" + "=" * 50)
    if success:
        print("✅ DIAGNÓSTICO CONCLUÍDO COM SUCESSO!")
        print("🎉 Servo motores estão funcionando!")
    else:
        print("❌ PROBLEMAS DETECTADOS!")
        print("🔧 Execute o modo interativo para investigar:")
        print("   python diagnose_servos.py interactive")

    print("\n💡 DICAS DE SOLUÇÃO:")
    print("   1. Verifique se os servos estão conectados aos pinos GPIO 1 e 3")
    print("   2. Certifique-se que os servos têm alimentação (5V)")
    print("   3. Teste calibração: python diagnose_servos.py interactive")
    print("   4. Verifique se o firmware foi carregado corretamente")

if __name__ == "__main__":
    main()