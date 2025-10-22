#!/usr/bin/env python3
"""
Script para registrar o Raspberry Pi no backend web
"""

import requests
import json
import socket
from datetime import datetime

def get_local_ip():
    """Obtém o IP local da máquina"""
    try:
        # Cria um socket para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conecta a um servidor externo
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Erro ao obter IP local: {e}")
        return "127.0.0.1"

def register_raspberry(backend_ip="192.168.0.134", backend_port=5000, raspberry_ip=None):
    """Registra o Raspberry Pi no backend"""

    if raspberry_ip is None:
        raspberry_ip = get_local_ip()
    print(f"IP do Raspberry Pi: {raspberry_ip}")

    # Dados do registro
    registration_data = {
        "ip": raspberry_ip,
        "port": 8080,  # Porta da API local do Raspberry Pi
        "status": {
            "battery": 100,
            "connected": True,
            "last_registration": datetime.now().isoformat()
        }
    }

    # URL do backend
    backend_url = f"http://{backend_ip}:{backend_port}/agv/register"

    try:
        print(f"Registrando Raspberry Pi no backend: {backend_url}")
        print(f"Dados: {json.dumps(registration_data, indent=2)}")

        response = requests.post(backend_url, json=registration_data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Raspberry Pi registrado com sucesso!")
                print(f"ID: {result.get('raspberry_id')}")
                return True
            else:
                print(f"❌ Erro no registro: {result.get('error')}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        print("Verifique se o backend está rodando e acessível")

    return False

if __name__ == "__main__":
    import sys
    
    raspberry_ip = None
    if len(sys.argv) > 1:
        raspberry_ip = sys.argv[1]
    
    print("🔧 Registrando Raspberry Pi no sistema AGV...")
    if raspberry_ip:
        print(f"Usando IP especificado: {raspberry_ip}")
    else:
        print("Detectando IP automaticamente...")
    
    success = register_raspberry(raspberry_ip=raspberry_ip)
    if success:
        print("🎉 Registro concluído! O Raspberry Pi agora pode receber comandos.")
    else:
        print("❌ Falha no registro. Verifique as configurações de rede.")