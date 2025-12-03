#!/usr/bin/env python3
"""
Sistema de descoberta automática do backend
Usa UDP broadcast para encontrar o servidor backend na rede local
"""

import socket
import json
import time
import threading
from typing import Optional, Tuple

class BackendDiscovery:
    """Cliente de descoberta do backend via UDP broadcast"""
    
    DISCOVERY_PORT = 37020  # Porta para broadcast
    DISCOVERY_MESSAGE = b"AGV_DISCOVERY_REQUEST"
    TIMEOUT = 5  # segundos
    
    def __init__(self):
        self.backend_ip = None
        self.backend_port = None
        self.last_discovery = None
        
    def discover_backend(self, timeout: int = TIMEOUT) -> Optional[Tuple[str, int]]:
        """
        Descobre o backend na rede enviando broadcast UDP
        
        Returns:
            Tuple[str, int]: (IP, porta) do backend ou None se não encontrado
        """
        print("🔍 Procurando backend na rede local...")
        
        try:
            # Criar socket UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            
            # Enviar broadcast
            broadcast_addr = ('<broadcast>', self.DISCOVERY_PORT)
            sock.sendto(self.DISCOVERY_MESSAGE, broadcast_addr)
            print(f"📡 Broadcast enviado na porta {self.DISCOVERY_PORT}")
            
            # Aguardar resposta
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = json.loads(data.decode('utf-8'))
                    
                    if response.get('service') == 'agv-backend':
                        self.backend_ip = response.get('ip', addr[0])
                        self.backend_port = response.get('port', 5000)
                        self.last_discovery = time.time()
                        
                        print(f"✅ Backend encontrado!")
                        print(f"   IP: {self.backend_ip}")
                        print(f"   Porta: {self.backend_port}")
                        
                        sock.close()
                        return (self.backend_ip, self.backend_port)
                        
                except socket.timeout:
                    continue
                except json.JSONDecodeError:
                    continue
            
            sock.close()
            print("❌ Backend não encontrado na rede")
            return None
            
        except Exception as e:
            print(f"❌ Erro na descoberta: {e}")
            return None
    
    def discover_with_retry(self, max_attempts: int = 3, retry_delay: int = 2) -> Optional[Tuple[str, int]]:
        """
        Tenta descobrir o backend com múltiplas tentativas
        
        Args:
            max_attempts: Número máximo de tentativas
            retry_delay: Delay entre tentativas em segundos
            
        Returns:
            Tuple[str, int]: (IP, porta) do backend ou None
        """
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 Tentativa {attempt}/{max_attempts}")
            result = self.discover_backend()
            
            if result:
                return result
            
            if attempt < max_attempts:
                print(f"⏳ Aguardando {retry_delay}s antes da próxima tentativa...")
                time.sleep(retry_delay)
        
        return None
    
    def get_backend_info(self) -> Optional[Tuple[str, int]]:
        """Retorna informações do último backend descoberto"""
        if self.backend_ip and self.backend_port:
            return (self.backend_ip, self.backend_port)
        return None


class BackendAnnouncer:
    """Servidor de anúncio do backend (roda no PC com backend)"""
    
    DISCOVERY_PORT = 37020
    DISCOVERY_MESSAGE = b"AGV_DISCOVERY_REQUEST"
    
    def __init__(self, backend_ip: str, backend_port: int):
        self.backend_ip = backend_ip
        self.backend_port = backend_port
        self.running = False
        self.thread = None
        
    def start(self):
        """Inicia servidor de anúncio em background"""
        if self.running:
            print("⚠️ Announcer já está rodando")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"📡 Backend Announcer iniciado na porta {self.DISCOVERY_PORT}")
        
    def stop(self):
        """Para servidor de anúncio"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("🛑 Backend Announcer parado")
        
    def _run(self):
        """Loop principal do servidor de anúncio"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.DISCOVERY_PORT))
            sock.settimeout(1)
            
            print(f"✅ Aguardando requisições de descoberta na porta {self.DISCOVERY_PORT}")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    
                    if data == self.DISCOVERY_MESSAGE:
                        print(f"📨 Requisição de descoberta recebida de {addr[0]}")
                        
                        # Preparar resposta
                        response = {
                            'service': 'agv-backend',
                            'ip': self.backend_ip,
                            'port': self.backend_port,
                            'timestamp': time.time()
                        }
                        
                        # Enviar resposta
                        sock.sendto(json.dumps(response).encode('utf-8'), addr)
                        print(f"✅ Resposta enviada para {addr[0]}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Só mostra erro se ainda estiver rodando
                        print(f"⚠️ Erro no announcer: {e}")
            
            sock.close()
            
        except Exception as e:
            print(f"❌ Erro fatal no announcer: {e}")


def get_local_ip() -> str:
    """Obtém o IP local da máquina"""
    try:
        # Conecta a um servidor externo para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"


# Testes
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Modo servidor (para testes no PC)
        print("🖥️ MODO SERVIDOR - Backend Announcer")
        print("="*50)
        
        local_ip = get_local_ip()
        port = 5000
        
        print(f"IP Local: {local_ip}")
        print(f"Porta Backend: {port}")
        
        announcer = BackendAnnouncer(local_ip, port)
        announcer.start()
        
        try:
            print("\n✅ Servidor rodando. Pressione Ctrl+C para parar...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Parando servidor...")
            announcer.stop()
    
    else:
        # Modo cliente (para Raspberry Pi)
        print("🤖 MODO CLIENTE - Backend Discovery")
        print("="*50)
        
        discovery = BackendDiscovery()
        result = discovery.discover_with_retry(max_attempts=3)
        
        if result:
            ip, port = result
            print(f"\n✅ BACKEND ENCONTRADO!")
            print(f"   Use estas configurações:")
            print(f"   IP: {ip}")
            print(f"   Porta: {port}")
        else:
            print("\n❌ Backend não encontrado após todas as tentativas")
