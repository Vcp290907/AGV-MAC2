#!/usr/bin/env python3
"""
Configuração centralizada do backend
Centraliza IP e porta do servidor backend para facilitar mudanças
"""

# Configurações do backend - ALTERE AQUI para mudar IP/porta
BACKEND_IP = '192.168.0.134'
BACKEND_PORT = 5000

def get_backend_ip():
    """Retorna o IP do backend"""
    return BACKEND_IP

def get_backend_port():
    """Retorna a porta do backend"""
    return BACKEND_PORT

def get_backend_url():
    """Retorna a URL completa do backend"""
    return f"http://{BACKEND_IP}:{BACKEND_PORT}"

def set_backend_ip(ip: str):
    """Altera o IP do backend (para uso dinâmico se necessário)"""
    global BACKEND_IP
    BACKEND_IP = ip

def set_backend_port(port: int):
    """Altera a porta do backend (para uso dinâmico se necessário)"""
    global BACKEND_PORT
    BACKEND_PORT = port

if __name__ == "__main__":
    print(f"Backend IP: {get_backend_ip()}")
    print(f"Backend Port: {get_backend_port()}")
    print(f"Backend URL: {get_backend_url()}")