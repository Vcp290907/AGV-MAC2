#!/usr/bin/env python3
"""
Teste simplificado usando ESP32Controller
Mesma abordagem que debug_serial.py mas através da classe
"""

import sys
import time
from esp32_control import ESP32Controller

def test_simple_connection():
    """Teste simples igual ao debug_serial.py"""
    print("🧪 TESTE SIMPLES DE CONEXÃO")
    print("=" * 30)

    # Criar controlador com porta específica
    controller = ESP32Controller(port='/dev/ttyACM0')

    print("📡 Conectando...")
    if not controller.connect():
        print("❌ Falha na conexão")
        return False

    print("✅ Conectado!")

    try:
        # Teste 1: Ping simples
        print("\n🧪 Teste 1: Ping simples")
        command = {'command': 'ping'}
        response = controller._send_command(command)
        print(f"📤 Comando: {command}")
        print(f"📨 Resposta: {response}")

        # Teste 2: Ping com timestamp
        print("\n🧪 Teste 2: Ping com timestamp")
        command = {'command': 'ping', 'timestamp': time.time()}
        response = controller._send_command(command)
        print(f"📤 Comando: {command}")
        print(f"📨 Resposta: {response}")

        # Teste 3: Status
        print("\n🧪 Teste 3: Status")
        status = controller.get_status()
        print(f"📊 Status: {status}")

        print("\n✅ Todos os testes concluídos!")
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

    finally:
        controller.disconnect()
        print("🔌 Desconectado")

def main():
    """Função principal"""
    success = test_simple_connection()

    if success:
        print("\n🎉 ESP32 funcionando corretamente!")
    else:
        print("\n❌ Problemas detectados")

if __name__ == "__main__":
    main()