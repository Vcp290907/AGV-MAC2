#!/usr/bin/env python3
"""
Backend Announcer - Servidor de anúncio UDP
Responde a requisições de descoberta do Raspberry Pi
"""

import socket
import json
import time
import threading


class BackendAnnouncer:
    """Servidor de anúncio do backend via UDP broadcast"""
    
    DISCOVERY_PORT = 37020
    DISCOVERY_MESSAGE = b"AGV_DISCOVERY_REQUEST"
    
    def __init__(self, backend_ip: str = None, backend_port: int = 5000):
        """
        Inicializa o announcer
        
        Args:
            backend_ip: IP do backend (se None, detecta automaticamente)
            backend_port: Porta do backend Flask
        """
        self.backend_ip = backend_ip or self._get_local_ip()
        self.backend_port = backend_port
        self.running = False
        self.thread = None
        self.request_count = 0
        
    def _get_local_ip(self) -> str:
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "0.0.0.0"
    
    def start(self):
        """Inicia servidor de anúncio em background"""
        if self.running:
            print("⚠️ Backend Announcer já está rodando")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"📡 Backend Announcer iniciado")
        print(f"   IP: {self.backend_ip}")
        print(f"   Porta Backend: {self.backend_port}")
        print(f"   Porta Discovery: {self.DISCOVERY_PORT}")
        
    def stop(self):
        """Para servidor de anúncio"""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print(f"🛑 Backend Announcer parado ({self.request_count} requisições atendidas)")
        
    def _run(self):
        """Loop principal do servidor de anúncio"""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Tentar bind em todas as interfaces
            sock.bind(('', self.DISCOVERY_PORT))
            sock.settimeout(1)
            
            print(f"✅ Aguardando requisições de descoberta na porta {self.DISCOVERY_PORT}")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    
                    if data == self.DISCOVERY_MESSAGE:
                        self.request_count += 1
                        print(f"📨 Requisição de descoberta #{self.request_count} de {addr[0]}")
                        
                        # Preparar resposta
                        response = {
                            'service': 'agv-backend',
                            'ip': self.backend_ip,
                            'port': self.backend_port,
                            'timestamp': time.time(),
                            'version': '1.0.0'
                        }
                        
                        # Enviar resposta
                        response_data = json.dumps(response).encode('utf-8')
                        sock.sendto(response_data, addr)
                        print(f"✅ Resposta enviada para {addr[0]} - Backend: {self.backend_ip}:{self.backend_port}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"⚠️ Erro ao processar requisição: {e}")
            
        except Exception as e:
            print(f"❌ Erro fatal no announcer: {e}")
        finally:
            if sock:
                sock.close()
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do announcer"""
        return {
            'running': self.running,
            'backend_ip': self.backend_ip,
            'backend_port': self.backend_port,
            'discovery_port': self.DISCOVERY_PORT,
            'request_count': self.request_count
        }


# Instância global
_announcer_instance = None

def get_announcer(backend_port: int = 5000) -> BackendAnnouncer:
    """Retorna instância global do announcer"""
    global _announcer_instance
    if _announcer_instance is None:
        _announcer_instance = BackendAnnouncer(backend_port=backend_port)
    return _announcer_instance

def start_announcer(backend_port: int = 5000):
    """Inicia o announcer"""
    announcer = get_announcer(backend_port)
    announcer.start()
    return announcer

def stop_announcer():
    """Para o announcer"""
    global _announcer_instance
    if _announcer_instance:
        _announcer_instance.stop()


# Testes
if __name__ == "__main__":
    print("🖥️ BACKEND ANNOUNCER - Teste")
    print("="*50)
    
    announcer = BackendAnnouncer(backend_port=5000)
    announcer.start()
    
    try:
        print("\n✅ Servidor rodando. Pressione Ctrl+C para parar...")
        print("💡 No Raspberry Pi, execute: python3 backend_discovery.py")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Parando servidor...")
        announcer.stop()
