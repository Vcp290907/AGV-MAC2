#!/usr/bin/env python3
import serial
import json
import time

print('🧪 Testando movimento para trás especificamente...')

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    print('✅ Porta aberta')

    # Testar movimento para trás
    move_cmd = {
        'comando': 'move',
        'direction': 'backward',
        'duration': 0.5,
        'timestamp': time.time()
    }
    ser.write((json.dumps(move_cmd) + '\n').encode('utf-8'))
    ser.flush()
    print(f'📤 Enviado movimento para trás: {json.dumps(move_cmd)}')

    # Ler resposta
    response = ser.readline().decode('utf-8').strip()
    print(f'📥 Resposta movimento: "{response}"')

    # Aguardar um pouco e testar stop
    time.sleep(0.5)

    stop_cmd = {'comando': 'stop', 'timestamp': time.time()}
    ser.write((json.dumps(stop_cmd) + '\n').encode('utf-8'))
    ser.flush()
    print(f'📤 Enviado stop: {json.dumps(stop_cmd)}')

    # Ler resposta do stop
    stop_response = ser.readline().decode('utf-8').strip()
    print(f'📥 Resposta stop: "{stop_response}"')

    ser.close()

except Exception as e:
    print(f'❌ Erro: {e}')