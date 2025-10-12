#!/usr/bin/env python3
import serial
import json
import time

print('🧪 Testando sequência completa de movimento para trás...')

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    print('✅ Porta aberta')

    # 1. Enviar comando de movimento
    move_cmd = {
        'comando': 'move',
        'direction': 'backward',
        'duration': 0.5,
        'timestamp': time.time()
    }
    ser.write((json.dumps(move_cmd) + '\n').encode('utf-8'))
    ser.flush()
    print(f'📤 Enviado movimento: {json.dumps(move_cmd)}')

    # 2. Ler resposta do movimento
    move_response = ser.readline().decode('utf-8').strip()
    print(f'📥 Resposta movimento: "{move_response}"')

    # 3. Aguardar duração
    print('⏱️  Aguardando 0.5s...')
    time.sleep(0.5)

    # 4. Enviar comando stop
    stop_cmd = {'comando': 'stop', 'timestamp': time.time()}
    ser.write((json.dumps(stop_cmd) + '\n').encode('utf-8'))
    ser.flush()
    print(f'📤 Enviado stop: {json.dumps(stop_cmd)}')

    # 5. Ler múltiplas respostas do stop (pode haver debug + status)
    responses = []
    for i in range(3):  # Tentar ler até 3 respostas
        try:
            response = ser.readline().decode('utf-8').strip()
            if response:
                responses.append(response)
                print(f'📥 Resposta {i+1}: "{response}"')
            else:
                break
        except:
            break
        time.sleep(0.1)  # Pequena pausa entre leituras

    ser.close()

    print(f'📊 Total de respostas recebidas: {len(responses)}')
    for i, resp in enumerate(responses):
        print(f'  {i+1}: {resp}')

except Exception as e:
    print(f'❌ Erro: {e}')