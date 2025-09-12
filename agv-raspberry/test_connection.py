#!/usr/bin/env python3
"""
Script de teste para verificar comunicação PC-Raspberry Pi
"""

import requests
import json
import time
from datetime import datetime

def test_pc_connection(pc_ip="192.168.0.134", pc_port=5000):
    """Testa conexão com o PC"""
    print("🧪 Testando conexão com PC...")

    try:
        url = f"http://{pc_ip}:{pc_port}/test"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✅ Conexão com PC estabelecida!")
            print(f"   Resposta: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Erro na resposta do PC: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão com PC: {e}")
        return False

def test_raspberry_api():
    """Testa API local do Raspberry Pi"""
    print("\n🧪 Testando API local do Raspberry Pi...")

    try:
        response = requests.get("http://localhost:8080/test", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✅ API local funcionando!")
            print(f"   Status: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Erro na API local: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ API local não está rodando: {e}")
        print("💡 Execute: python main.py")
        return False

def test_full_communication(pc_ip="192.168.0.134", pc_port=5000):
    """Testa comunicação completa"""
    print("\n🔄 Testando comunicação completa PC ↔ Raspberry Pi...")

    # Testar registro do Raspberry Pi
    try:
        register_data = {
            'ip': '192.168.0.100',  # IP do Raspberry (exemplo)
            'port': 8080,
            'status': {
                'battery': 85,
                'position': {'x': 0, 'y': 0, 'orientation': 0},
                'status': 'idle'
            },
            'timestamp': datetime.now().isoformat()
        }

        url = f"http://{pc_ip}:{pc_port}/agv/register"
        response = requests.post(url, json=register_data, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Registro do Raspberry Pi realizado!")
                raspberry_id = data.get('raspberry_id')
                print(f"   ID: {raspberry_id}")
                return True
            else:
                print(f"❌ Falha no registro: {data.get('error')}")
                return False
        else:
            print(f"❌ Erro no registro: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na comunicação: {e}")
        return False

def test_status_update(pc_ip="192.168.0.134", pc_port=5000):
    """Testa envio de status"""
    print("\n📊 Testando envio de status...")

    try:
        status_data = {
            'agv_id': 'AGV_01',
            'status': {
                'battery': 90,
                'position': {'x': 10, 'y': 20, 'orientation': 45},
                'speed': 0.5,
                'status': 'moving',
                'last_update': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }

        url = f"http://{pc_ip}:{pc_port}/agv/status"
        response = requests.post(url, json=status_data, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Status enviado com sucesso!")
                return True
            else:
                print(f"❌ Falha no envio: {data.get('error')}")
                return False
        else:
            print(f"❌ Erro no envio: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na comunicação: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes de comunicação AGV")
    print("=" * 50)

    pc_ip = input("Digite o IP do PC (padrão: 192.168.0.134): ").strip() or "192.168.0.134"
    pc_port = 5000

    print(f"\nConfiguração:")
    print(f"  PC IP: {pc_ip}")
    print(f"  PC Port: {pc_port}")
    print(f"  Raspberry IP: localhost")
    print(f"  Raspberry Port: 8080")

    # Executar testes
    tests = [
        ("Conexão com PC", lambda: test_pc_connection(pc_ip, pc_port)),
        ("API local Raspberry", test_raspberry_api),
        ("Registro Raspberry", lambda: test_full_communication(pc_ip, pc_port)),
        ("Envio de status", lambda: test_status_update(pc_ip, pc_port))
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Executando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"Resultado: {status}")
        except Exception as e:
            print(f"❌ ERRO: {e}")
            results.append((test_name, False))

        time.sleep(1)  # Pequena pausa entre testes

    # Resumo final
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1

    print(f"\n📊 Total: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 Todos os testes passaram! Comunicação funcionando perfeitamente.")
    elif passed >= total * 0.75:
        print("⚠️  Maioria dos testes passou. Verifique configurações.")
    else:
        print("❌ Muitos testes falharam. Verifique configuração de rede.")

    print("\n💡 Dicas de troubleshooting:")
    print("   - Verifique se o backend do PC está rodando (python app.py)")
    print("   - Verifique se o Raspberry Pi está na mesma rede WiFi")
    print("   - Teste ping entre PC e Raspberry Pi")
    print("   - Verifique portas 5000 (PC) e 8080 (Raspberry)")

if __name__ == "__main__":
    main()