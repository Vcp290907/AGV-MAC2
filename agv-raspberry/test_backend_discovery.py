#!/usr/bin/env python3
"""
Script de teste para descoberta automática do backend
Execute no Raspberry Pi para testar a funcionalidade
"""

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend_discovery import BackendDiscovery
from backend_config import get_backend_ip, get_backend_port, get_backend_url, clear_cache

def main():
    print("🧪 TESTE DE DESCOBERTA AUTOMÁTICA DO BACKEND")
    print("="*60)
    
    # Limpar cache
    print("\n1️⃣ Limpando cache...")
    clear_cache()
    print("✅ Cache limpo")
    
    # Teste 1: Descoberta básica
    print("\n2️⃣ Teste de descoberta básica (5 segundos)...")
    discovery = BackendDiscovery()
    result = discovery.discover_backend(timeout=5)
    
    if result:
        ip, port = result
        print(f"✅ Backend encontrado!")
        print(f"   IP: {ip}")
        print(f"   Porta: {port}")
    else:
        print("❌ Backend não encontrado")
        print("\n💡 Certifique-se de que:")
        print("   1. O backend está rodando no PC")
        print("   2. Raspberry Pi e PC estão na mesma rede")
        print("   3. Firewall não está bloqueando a porta 37020 (UDP)")
        return False
    
    # Teste 2: Descoberta com retry
    print("\n3️⃣ Teste de descoberta com retry (3 tentativas)...")
    clear_cache()
    result = discovery.discover_with_retry(max_attempts=3, retry_delay=2)
    
    if result:
        print(f"✅ Backend encontrado com retry: {result[0]}:{result[1]}")
    else:
        print("❌ Falha mesmo com retry")
        return False
    
    # Teste 3: Usando backend_config
    print("\n4️⃣ Teste usando backend_config.py...")
    clear_cache()
    
    ip = get_backend_ip()
    port = get_backend_port()
    url = get_backend_url()
    
    print(f"✅ Configuração obtida:")
    print(f"   IP: {ip}")
    print(f"   Porta: {port}")
    print(f"   URL: {url}")
    
    # Teste 4: Conexão HTTP
    print("\n5️⃣ Testando conexão HTTP...")
    try:
        import requests
        response = requests.get(f"{url}/status", timeout=5)
        if response.status_code == 200:
            print(f"✅ Conexão HTTP bem-sucedida!")
            print(f"   Status: {response.json()}")
        else:
            print(f"⚠️ Status HTTP: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão HTTP: {e}")
        return False
    
    # Teste 5: Endpoint de discovery status
    print("\n6️⃣ Testando endpoint /discovery/status...")
    try:
        response = requests.get(f"{url}/discovery/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint funcionando!")
            if data.get('success'):
                stats = data.get('announcer', {})
                print(f"   Announcer rodando: {stats.get('running')}")
                print(f"   Requisições atendidas: {stats.get('request_count')}")
        else:
            print(f"⚠️ Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Endpoint não disponível: {e}")
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("="*60)
    print("\n💡 A descoberta automática está funcionando corretamente.")
    print("   O arquivo agv_mission_control.py usará automaticamente")
    print("   o IP descoberto ao invés do IP fixo configurado.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
