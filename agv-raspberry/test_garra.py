#!/usr/bin/env python3
from esp32_control import connect_esp32_garra, move_servos_esp32

print("Testando conexão com ESP32 garra...")
if connect_esp32_garra():
    print("✅ Conectado!")
    # Teste simples: mover servo
    result = move_servos_esp32({"giro": 90, "um": 90, "dois": 90, "garra": 90, "servo3": 90})
    print("Resultado:", result)
else:
    print("❌ Falha na conexão")