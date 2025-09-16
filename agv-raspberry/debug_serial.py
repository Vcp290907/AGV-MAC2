#!/usr/bin/env python3
"""
Script de debug para comunicação serial com ESP32
Mostra exatamente o que é enviado e recebido
"""

import serial
import time
import json

def debug_serial_communication(port='/dev/ttyACM0', baudrate=115200):
    """Debug detalhado da comunicação serial"""
    print("🔧 DEBUG SERIAL ESP32")
    print("=" * 40)
    print(f"Porta: {port}")
    print(f"Baudrate: {baudrate}")
    print()

    try:
        # Abrir porta serial
        print("📡 Abrindo porta serial...")
        ser = serial.Serial(port, baudrate, timeout=2)
        print("✅ Porta aberta com sucesso")
        print()

        # Aguardar ESP32 inicializar
        print("⏳ Aguardando ESP32 inicializar...")
        time.sleep(3)

        # Ler qualquer mensagem inicial
        if ser.in_waiting > 0:
            initial_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print("📨 Mensagem inicial do ESP32:")
            print(f"   '{initial_data.strip()}'")
            print()

        # Teste 1: Ping simples
        print("🧪 TESTE 1: Ping simples")
        test_command = {"command": "ping"}
        json_str = json.dumps(test_command)

        print(f"📤 Enviando: {json_str}")
        ser.write((json_str + '\n').encode('utf-8'))
        ser.flush()

        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"📨 Resposta: '{response}'")
        else:
            print("❌ Nenhuma resposta recebida")
        print()

        # Teste 2: Ping com timestamp (como o detector)
        print("🧪 TESTE 2: Ping com timestamp (como detector)")
        test_command = {"command": "ping", "timestamp": time.time()}
        json_str = json.dumps(test_command)

        print(f"📤 Enviando: {json_str}")
        ser.write((json_str + '\n').encode('utf-8'))
        ser.flush()

        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"📨 Resposta: '{response}'")
        else:
            print("❌ Nenhuma resposta recebida")
        print()

        # Teste 3: Comando inválido
        print("🧪 TESTE 3: Comando inválido")
        test_command = {"invalid": "command"}
        json_str = json.dumps(test_command)

        print(f"📤 Enviando: {json_str}")
        ser.write((json_str + '\n').encode('utf-8'))
        ser.flush()

        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"📨 Resposta: '{response}'")
        else:
            print("❌ Nenhuma resposta recebida")
        print()

        # Teste 4: Dados crus
        print("🧪 TESTE 4: Dados crus (sem JSON)")
        raw_data = "HELLO ESP32\n"
        print(f"📤 Enviando dados crus: {repr(raw_data)}")
        ser.write(raw_data.encode('utf-8'))
        ser.flush()

        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"📨 Resposta: '{response.strip()}'")
        else:
            print("❌ Nenhuma resposta recebida")
        print()

        # Fechar conexão
        ser.close()
        print("🔌 Conexão fechada")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal"""
    import sys

    port = '/dev/ttyACM0'  # Porta padrão

    if len(sys.argv) > 1:
        port = sys.argv[1]

    debug_serial_communication(port)

if __name__ == "__main__":
    main()