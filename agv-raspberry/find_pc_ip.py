#!/usr/bin/env python3
"""
Script para descobrir automaticamente o IP do PC na rede
"""

import socket
import subprocess
import platform
import netifaces
import ipaddress
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_local_ip():
    """Obtém o IP local do Raspberry Pi"""
    try:
        # Cria um socket para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conecta ao Google DNS
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"❌ Erro ao obter IP local: {e}")
        return None

def get_network_info():
    """Obtém informações da rede"""
    try:
        local_ip = get_local_ip()
        if not local_ip:
            return None

        # Calcula a rede
        ip_obj = ipaddress.IPv4Address(local_ip)
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)

        return {
            'local_ip': local_ip,
            'network': str(network.network_address),
            'netmask': str(network.netmask),
            'broadcast': str(network.broadcast_address)
        }
    except Exception as e:
        print(f"❌ Erro ao obter informações de rede: {e}")
        return None

def scan_port(ip, port, timeout=1):
    """Testa se uma porta está aberta em um IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def find_pc_in_network(network_info, pc_port=5000, max_workers=20):
    """Procura pelo PC na rede testando a porta específica"""
    if not network_info:
        return []

    network = ipaddress.IPv4Network(f"{network_info['network']}/24", strict=False)
    local_ip = network_info['local_ip']

    print(f"🔍 Procurando PC na rede {network}...")
    print(f"📡 Testando porta {pc_port}...")
    print("⏳ Isso pode levar alguns segundos...\n")

    found_ips = []

    def check_ip(ip):
        if str(ip) == local_ip:
            return None  # Pula o próprio IP

        if scan_port(str(ip), pc_port, timeout=0.5):
            return str(ip)
        return None

    # Testa IPs em paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_ip, ip) for ip in network.hosts()]

        for future in as_completed(futures):
            result = future.result()
            if result:
                found_ips.append(result)
                print(f"✅ PC encontrado: {result}:{pc_port}")

    return found_ips

def test_pc_connection(pc_ip, pc_port=5000):
    """Testa a conexão com o PC encontrado"""
    try:
        print(f"\n🧪 Testando conexão com {pc_ip}:{pc_port}...")

        # Testa conectividade básica
        if not scan_port(pc_ip, pc_port, timeout=2):
            print("❌ Porta não responde")
            return False

        # Testa endpoint de teste
        import requests
        try:
            response = requests.get(f"http://{pc_ip}:{pc_port}/test", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Conexão bem-sucedida!")
                print(f"   Resposta: {data.get('message', 'OK')}")
                return True
            else:
                print(f"❌ Resposta HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def get_network_interfaces():
    """Obtém informações das interfaces de rede"""
    try:
        interfaces = {}
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr')
                    if ip and not ip.startswith('127.'):
                        interfaces[interface] = {
                            'ip': ip,
                            'netmask': addr.get('netmask'),
                            'broadcast': addr.get('broadcast')
                        }
        return interfaces
    except:
        return {}

def main():
    """Função principal"""
    print("🔍 DESCOBRIDOR DE IP DO PC - Sistema AGV")
    print("=" * 50)

    # Obtém informações da rede
    print("📡 Obtendo informações da rede...")
    network_info = get_network_info()

    if not network_info:
        print("❌ Não foi possível obter informações da rede")
        print("\n💡 Verifique sua conexão WiFi")
        return

    print("✅ Informações da rede obtidas:")
    print(f"   IP Local: {network_info['local_ip']}")
    print(f"   Rede: {network_info['network']}/24")
    print(f"   Broadcast: {network_info['broadcast']}")

    # Mostra interfaces de rede
    interfaces = get_network_interfaces()
    if interfaces:
        print("\n🔌 Interfaces de rede encontradas:")
        for name, info in interfaces.items():
            print(f"   {name}: {info['ip']}")

    # Procura pelo PC na rede
    print("Procurando PC na rede..."    found_ips = find_pc_in_network(network_info)

    if not found_ips:
        print("\n❌ Nenhum PC encontrado na rede")
        print("\n💡 Possíveis soluções:")
        print("   1. Verifique se o PC está ligado")
        print("   2. Verifique se o backend está rodando (python app.py)")
        print("   3. Verifique se estão na mesma rede WiFi")
        print("   4. Tente executar no PC: netstat -tlnp | grep :5000")
        return

    print(f"\n🎉 Encontrado(s) {len(found_ips)} PC(s) na rede!")

    # Testa conexão com PCs encontrados
    working_pcs = []
    for pc_ip in found_ips:
        if test_pc_connection(pc_ip):
            working_pcs.append(pc_ip)

    if working_pcs:
        print("
✅ PC(s) funcional(is):"        for i, pc_ip in enumerate(working_pcs, 1):
            print(f"   {i}. {pc_ip}:5000")

        if len(working_pcs) == 1:
            pc_ip = working_pcs[0]
            print("
📝 CONFIGURAÇÃO RECOMENDADA:"            print(f"   Adicione no config.py ou /home/pi/agv_config.json:")
            print(f'   "pc_ip": "{pc_ip}"')
            print(f'   "pc_port": 5000')

            # Oferece atualizar automaticamente
            update_auto = input(f"\n🤖 Deseja atualizar config.py automaticamente com {pc_ip}? (y/N): ")
            if update_auto.lower() in ['y', 'yes', 's', 'sim']:
                try:
                    with open('config.py', 'r') as f:
                        content = f.read()

                    # Substitui o IP do PC
                    import re
                    new_content = re.sub(
                        r'pc_ip\s*:\s*["\'][^"\']*["\']',
                        f'pc_ip: "{pc_ip}"',
                        content
                    )

                    with open('config.py', 'w') as f:
                        f.write(new_content)

                    print(f"✅ config.py atualizado com IP: {pc_ip}")

                except Exception as e:
                    print(f"❌ Erro ao atualizar config.py: {e}")
                    print(f"   Atualize manualmente: pc_ip = '{pc_ip}'")
        else:
            print("
📝 Vários PCs encontrados. Configure manualmente:"            print("   Edite config.py e defina pc_ip com o IP correto")
    else:
        print("\n❌ Nenhum PC responde corretamente")
        print("   Verifique se o backend Flask está rodando no PC")

if __name__ == "__main__":
    main()