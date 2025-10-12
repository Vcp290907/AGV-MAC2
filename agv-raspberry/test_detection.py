#!/usr/bin/env python3
import serial
import json
import time

print('🧪 Testando detecção automática...')

# Simular o teste do _test_port
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    print('✅ Porta aberta')

    # Enviar ping como no código
    ping_cmd = {'comando': 'ping', 'timestamp': time.time()}
    ser.write((json.dumps(ping_cmd) + '\n').encode('utf-8'))
    ser.flush()
    print(f'📤 Enviado: {json.dumps(ping_cmd)}')

    # Ler resposta
    response = ser.readline().decode('utf-8').strip()
    print(f'📥 Resposta crua: "{response}"')

    ser.close()

    # Testar parsing JSON
    if response:
        try:
            response_data = json.loads(response)
            print(f'📥 Resposta JSON: {response_data}')
            if response_data.get('status') in ['ok', 'success']:
                print('✅ Detecção funcionaria!')
            else:
                print('❌ Status não reconhecido')
        except json.JSONDecodeError as e:
            print(f'❌ Resposta não é JSON válido: {e}')
    else:
        print('❌ Nenhuma resposta')

except Exception as e:
    print(f'❌ Erro: {e}')