#!/usr/bin/env python3
"""
Guia dos próximos passos após descobrir o IP do PC
"""

import os
import json
import requests
import time
from datetime import datetime

def check_config():
    """Verifica se a configuração está correta"""
    print("🔍 Verificando configuração...")

    try:
        # Tenta ler config.py
        with open('config.py', 'r') as f:
            config_content = f.read()

        # Procura pelo IP do PC
        import re
        pc_ip_match = re.search(r'pc_ip\s*[:=]\s*["\']([^"\']+)["\']', config_content)

        if pc_ip_match:
            pc_ip = pc_ip_match.group(1)
            print(f"✅ IP do PC configurado: {pc_ip}")
            return pc_ip
        else:
            print("❌ IP do PC não encontrado em config.py")
            return None

    except FileNotFoundError:
        print("❌ Arquivo config.py não encontrado")
        return None
    except Exception as e:
        print(f"❌ Erro ao ler config.py: {e}")
        return None

def test_connection(pc_ip, pc_port=5000):
    """Testa conexão com o PC"""
    print(f"\n🧪 Testando conexão com {pc_ip}:{pc_port}...")

    try:
        # Teste básico de conectividade
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((pc_ip, pc_port))
        sock.close()

        if result != 0:
            print("❌ Porta 5000 não está acessível")
            return False

        # Teste da API
        response = requests.get(f"http://{pc_ip}:{pc_port}/test", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Conexão com PC estabelecida!")
            print(f"   Status: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Resposta HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def register_raspberry(pc_ip, pc_port=5000):
    """Registra o Raspberry Pi no PC"""
    print("
📝 Registrando Raspberry Pi no PC..."    try:
        register_data = {
            'ip': get_local_ip(),
            'port': 8080,
            'status': {
                'battery': 85,
                'position': {'x': 0, 'y': 0, 'orientation': 0},
                'status': 'idle'
            },
            'timestamp': datetime.now().isoformat()
        }

        response = requests.post(
            f"http://{pc_ip}:{pc_port}/agv/register",
            json=register_data,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                raspberry_id = data.get('raspberry_id')
                print("✅ Raspberry Pi registrado com sucesso!")
                print(f"   ID: {raspberry_id}")
                return True
            else:
                print(f"❌ Falha no registro: {data.get('error')}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Erro no registro: {e}")
        return False

def get_local_ip():
    """Obtém IP local do Raspberry Pi"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def start_agv_system():
    """Inicia o sistema AGV"""
    print("
🚀 Iniciando sistema AGV..."    try:
        # Verifica se já está rodando
        import subprocess
        result = subprocess.run(
            ['pgrep', '-f', 'main.py'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("⚠️  Sistema já está rodando")
            print("   Para parar: curl -X POST http://localhost:8080/shutdown")
            return True

        # Inicia em background
        print("   Executando: python main.py &")
        os.system("python main.py &")

        # Aguarda um pouco
        time.sleep(3)

        # Testa se iniciou
        try:
            response = requests.get("http://localhost:8080/status", timeout=5)
            if response.status_code == 200:
                print("✅ Sistema AGV iniciado com sucesso!")
                print("   API local: http://localhost:8080")
                return True
            else:
                print("❌ Sistema iniciou mas API não responde")
                return False
        except:
            print("❌ Sistema não iniciou corretamente")
            return False

    except Exception as e:
        print(f"❌ Erro ao iniciar sistema: {e}")
        return False

def show_next_steps(pc_ip):
    """Mostra próximos passos"""
    print("
🎯 PRÓXIMOS PASSOS:"    print("=" * 50)
    print("
1. 🖥️  NO PC (mantenha rodando):"    print("   python app.py"    print("   # Backend deve estar rodando na porta 5000"    print("
2. 🤖 NO RASPBERRY PI (já configurado):"    print("   Sistema AGV rodando em background"    print("   API local: http://localhost:8080"    print("
3. 🌐 ACESSO AO SISTEMA:"    print(f"   Web Interface: http://{pc_ip}:5000"    print("   Mobile App: Use o app instalado"    print("
4. 📊 MONITORAMENTO:"    print("   Ver logs: tail -f /var/log/agv_system.log"    print("   Status API: curl http://localhost:8080/status"    print("
5. 🧪 TESTES:"    print("   Teste comunicação: python test_connection.py"    print("   Teste movimento: Use interface web"    print("
6. 🔧 MANUTENÇÃO:"    print("   Parar sistema: curl -X POST http://localhost:8080/shutdown"    print("   Reiniciar: python main.py &"    print("
📋 FUNCIONALIDADES DISPONÍVEIS:"    print("   ✅ Comunicação PC ↔ Raspberry Pi"    print("   ✅ Interface web completa"    print("   ✅ App mobile"    print("   ⏳ ESP32 + motores (próxima fase)"    print("   ⏳ Visão computacional (próxima fase)"    print("   ⏳ Navegação autônoma (próxima fase)"    print("
🎉 SISTEMA AGV OPERACIONAL!"    print("
💡 DICAS:"    print("   - Mantenha PC e Raspberry na mesma rede WiFi"    print("   - Monitore logs para detectar problemas"    print("   - Use interface web para controlar AGV"    print("   - Teste funcionalidades gradualmente"    print("
🚨 EM CASO DE PROBLEMAS:"    print("   1. Verifique se PC está acessível: ping " + pc_ip)
    print("   2. Teste comunicação: python test_connection.py"    print("   3. Verifique logs: tail -f /var/log/agv_system.log"    print("   4. Consulte: cat TROUBLESHOOTING.md"    print("
🎊 Parabéns! Seu sistema AGV está pronto para uso!"def main():
    """Função principal"""
    print("🎯 GUIA DOS PRÓXIMOS PASSOS - Sistema AGV")
    print("=" * 50)

    # Verifica configuração
    pc_ip = check_config()
    if not pc_ip:
        print("
❌ Configuração incompleta!"        print("Execute primeiro: python find_pc_ip.py"        return

    # Testa conexão
    if not test_connection(pc_ip):
        print("
❌ Problema de conectividade!"        print("Verifique se o PC está ligado e o backend rodando"        return

    # Registra Raspberry Pi
    if not register_raspberry(pc_ip):
        print("
❌ Falha no registro!"        print("Verifique conectividade e tente novamente"        return

    # Inicia sistema AGV
    if not start_agv_system():
        print("
❌ Falha ao iniciar sistema!"        print("Verifique logs e tente novamente"        return

    # Mostra próximos passos
    show_next_steps(pc_ip)

if __name__ == "__main__":
    main()