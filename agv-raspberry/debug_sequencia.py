#!/usr/bin/env python3
from agv_mission_control import AGVMissionControl

print("Executando sequência teste_garra.json...")
mc = AGVMissionControl()
result = mc.executar_sequencia("teste_garra.json")
print("Resultado:", result)