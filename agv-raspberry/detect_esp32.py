#!/usr/bin/env python3
"""
Script para detectar automaticamente portas USB do ESP32
"""

import serial
import serial.tools.list_ports
import time
import sys

def list_usb_ports():
    """Lista todas as portas USB disponíveis"""
    ports = serial.tools.list_ports.comports()
    usb_ports = []

    print("🔍 Procurando portas USB disponíveis...")

    for port in ports:
        if 'USB' in port.device or 'ACM' in port.device:
            usb_ports.append(port.device)
            print(f"   📡 Porta encontrada: {port.device} - {port.description}")

    if not usb_ports:
        print("   ❌ Nenhuma porta USB encontrada")
        return []

    return usb_ports

def test_port(port, baudrate=115200, timeout=2):
    """Testa se uma porta específica responde como ESP32"""
    try:
        print(f"   🧪 Testando porta {port}...")

        # Tentar abrir a porta
        ser = serial.Serial(port, baudrate, timeout=timeout)

        # Aguardar um pouco para estabilizar
        time.sleep(1)

        # Enviar comando de ping
        ping_command = '{"command": "ping", "timestamp": ' + str(time.time()) + '}\n'
        ser.write(ping_command.encode('utf-8'))
        ser.flush()

        # Aguardar resposta
        response = ser.readline().decode('utf-8').strip()

        ser.close()

        if response:
            print(f"   ✅ Resposta recebida: {response}")
            return True
        else:
            print(f"   ⚠️  Porta responde mas sem dados JSON")
            return False

    except serial.SerialException as e:
        print(f"   ❌ Erro na porta {port}: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro inesperado na porta {port}: {e}")
        return False

def find_esp32_port():
    """Procura automaticamente pela porta do ESP32"""
    print("🤖 Procurando ESP32 conectado...\n")

    usb_ports = list_usb_ports()

    if not usb_ports:
        print("\n❌ Nenhum dispositivo USB encontrado!")
        print("💡 Verifique se o ESP32 está conectado e ligado")
        return None

    print(f"\n🧪 Testando {len(usb_ports)} porta(s) encontrada(s)...\n")

    for port in usb_ports:
        if test_port(port):
            print(f"\n🎉 ESP32 encontrado na porta: {port}")
            return port

        print()  # Linha em branco entre testes

    print("❌ ESP32 não encontrado em nenhuma porta USB")
    print("💡 Possíveis causas:")
    print("   - ESP32 não está conectado")
    print("   - ESP32 não tem o firmware correto carregado")
    print("   - Porta USB diferente (verificar com 'ls /dev/tty*')")
    print("   - Problemas de permissão (verificar com 'sudo usermod -a -G dialout $USER')")

    return None

def check_permissions():
    """Verifica se o usuário tem permissões para acessar portas USB"""
    print("🔐 Verificando permissões de acesso USB...")

    try:
        # Tentar listar portas USB
        ports = serial.tools.list_ports.comports()
        print("   ✅ Permissões OK - conseguiu listar portas USB")
        return True
    except Exception as e:
        print(f"   ❌ Problema de permissões: {e}")
        print("   💡 Solução: sudo usermod -a -G dialout $USER")
        print("   💡 Depois faça logout e login novamente")
        return False

def main():
    """Função principal"""
    print("🔍 DETECTOR DE ESP32")
    print("=" * 30)

    # Verificar permissões primeiro
    if not check_permissions():
        print("\n❌ Corrija as permissões primeiro!")
        sys.exit(1)

    # Procurar ESP32
    esp32_port = find_esp32_port()

    if esp32_port:
        print(f"\n✅ ESP32 detectado com sucesso!")
        print(f"📍 Porta: {esp32_port}")
        print(f"\n💡 Use esta porta nos seus scripts:")
        print(f"   export ESP32_PORT={esp32_port}")
        print(f"   python test_esp32_connection.py basic --port {esp32_port}")

        # Salvar em arquivo de configuração se possível
        try:
            with open('esp32_port.txt', 'w') as f:
                f.write(esp32_port)
            print(f"   💾 Porta salva em esp32_port.txt")
        except:
            pass

        return esp32_port
    else:
        print("\n❌ ESP32 não encontrado!")
        print("\n🔧 Passos para resolver:")
        print("   1. Conecte o ESP32 ao Raspberry Pi")
        print("   2. Certifique-se que está ligado (LED aceso)")
        print("   3. Carregue o firmware esp32_motor_control.ino")
        print("   4. Execute: sudo usermod -a -G dialout $USER")
        print("   5. Faça logout e login novamente")
        print("   6. Execute este script novamente")

        sys.exit(1)

if __name__ == "__main__":
    main()