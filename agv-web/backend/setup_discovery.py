#!/usr/bin/env python3
"""
Script de configuração para descoberta automática do backend
Execute no PC onde o backend roda para configurar firewall
"""

import os
import sys
import platform
import subprocess

def is_admin():
    """Verifica se o script está rodando como admin"""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False

def configure_windows_firewall():
    """Configura firewall do Windows"""
    print("🔧 Configurando Firewall do Windows...")
    
    rule_name = "AGV Backend Discovery"
    port = "37020"
    
    # Remover regra antiga se existir
    try:
        subprocess.run(
            f'netsh advfirewall firewall delete rule name="{rule_name}"',
            shell=True,
            capture_output=True
        )
    except:
        pass
    
    # Adicionar nova regra
    cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=UDP localport={port}'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Regra de firewall adicionada com sucesso!")
            print(f"   Porta UDP {port} liberada para descoberta")
            return True
        else:
            print(f"❌ Erro ao adicionar regra: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def configure_linux_firewall():
    """Configura firewall do Linux (ufw)"""
    print("🔧 Configurando Firewall do Linux (UFW)...")
    
    port = "37020"
    
    try:
        # Verificar se ufw está instalado
        result = subprocess.run("which ufw", shell=True, capture_output=True)
        if result.returncode != 0:
            print("⚠️ UFW não está instalado. Firewall pode precisar configuração manual.")
            return False
        
        # Adicionar regra
        cmd = f"ufw allow {port}/udp"
        result = subprocess.run(f"sudo {cmd}", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Regra de firewall adicionada com sucesso!")
            print(f"   Porta UDP {port} liberada para descoberta")
            return True
        else:
            print(f"❌ Erro ao adicionar regra: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def get_local_ip():
    """Obtém IP local"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Desconhecido"

def test_backend():
    """Testa se o backend está rodando"""
    import socket
    
    print("\n🧪 Testando conexão com backend...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("✅ Backend está rodando na porta 5000")
            return True
        else:
            print("⚠️ Backend não está rodando na porta 5000")
            print("   Inicie o backend com: python app.py")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar backend: {e}")
        return False

def main():
    print("="*60)
    print("🚀 CONFIGURAÇÃO DE DESCOBERTA AUTOMÁTICA DO BACKEND")
    print("="*60)
    
    system = platform.system()
    local_ip = get_local_ip()
    
    print(f"\n📊 Informações do Sistema:")
    print(f"   Sistema Operacional: {system}")
    print(f"   IP Local: {local_ip}")
    
    # Verificar se é admin
    if not is_admin():
        print("\n⚠️ ATENÇÃO: Este script precisa de privilégios administrativos!")
        if system == "Windows":
            print("   Execute como Administrador (clique direito -> 'Executar como administrador')")
        else:
            print("   Execute com sudo: sudo python3 setup_discovery.py")
        
        # Perguntar se deseja continuar sem admin
        resp = input("\nContinuar mesmo assim? (s/N): ").lower()
        if resp != 's':
            print("❌ Configuração cancelada")
            return 1
    
    # Configurar firewall
    print(f"\n🔧 Configurando firewall para {system}...")
    
    if system == "Windows":
        success = configure_windows_firewall()
    elif system == "Linux":
        success = configure_linux_firewall()
    else:
        print(f"⚠️ Sistema {system} não suportado automaticamente")
        print("   Configure manualmente a porta UDP 37020")
        success = False
    
    if not success:
        print("\n💡 Configuração manual necessária:")
        print("   Libere a porta UDP 37020 no seu firewall")
    
    # Testar backend
    test_backend()
    
    # Instruções finais
    print("\n" + "="*60)
    print("✅ CONFIGURAÇÃO CONCLUÍDA")
    print("="*60)
    print("\n📝 Próximos passos:")
    print("   1. Inicie o backend: cd agv-web/backend && python app.py")
    print("   2. No Raspberry Pi: python3 test_backend_discovery.py")
    print("   3. Execute o AGV: python3 agv_mission_control.py")
    print("\n💡 O Raspberry Pi descobrirá automaticamente o IP do backend!")
    print(f"   IP do PC: {local_ip}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Configuração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
