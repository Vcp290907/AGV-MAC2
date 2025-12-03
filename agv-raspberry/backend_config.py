#!/usr/bin/env python3
"""
Configuração centralizada do backend
Centraliza IP e porta do servidor backend para facilitar mudanças
Suporta descoberta automática via UDP broadcast
"""

import os
import json
from typing import Optional, Tuple

# Configurações do backend - ALTERE AQUI para mudar IP/porta (fallback)
BACKEND_IP = '192.168.0.134'
BACKEND_PORT = 5000

# Cache do backend descoberto
_cached_backend_ip = None
_cached_backend_port = None
_auto_discovery_enabled = True

def enable_auto_discovery(enabled: bool = True):
    """Ativa/desativa descoberta automática"""
    global _auto_discovery_enabled
    _auto_discovery_enabled = enabled

def discover_backend_auto() -> Optional[Tuple[str, int]]:
    """
    Tenta descobrir o backend automaticamente
    
    Returns:
        Tuple[str, int]: (IP, porta) ou None se não encontrado
    """
    if not _auto_discovery_enabled:
        return None
    
    try:
        from backend_discovery import BackendDiscovery
        
        discovery = BackendDiscovery()
        result = discovery.discover_with_retry(max_attempts=2, retry_delay=1)
        
        if result:
            global _cached_backend_ip, _cached_backend_port
            _cached_backend_ip, _cached_backend_port = result
            print(f"✅ Backend descoberto automaticamente: {_cached_backend_ip}:{_cached_backend_port}")
            return result
        
    except Exception as e:
        print(f"⚠️ Falha na descoberta automática: {e}")
    
    return None

def get_backend_ip() -> str:
    """
    Retorna o IP do backend
    Tenta descoberta automática se não houver cache
    """
    global _cached_backend_ip
    
    # Se já temos cache, usar
    if _cached_backend_ip:
        return _cached_backend_ip
    
    # Tentar descoberta automática
    if _auto_discovery_enabled:
        result = discover_backend_auto()
        if result:
            return result[0]
    
    # Fallback para IP configurado
    return BACKEND_IP

def get_backend_port() -> int:
    """
    Retorna a porta do backend
    Tenta descoberta automática se não houver cache
    """
    global _cached_backend_port
    
    # Se já temos cache, usar
    if _cached_backend_port:
        return _cached_backend_port
    
    # Tentar descoberta automática
    if _auto_discovery_enabled:
        result = discover_backend_auto()
        if result:
            return result[1]
    
    # Fallback para porta configurada
    return BACKEND_PORT

def get_backend_url() -> str:
    """Retorna a URL completa do backend"""
    ip = get_backend_ip()
    port = get_backend_port()
    return f"http://{ip}:{port}"

def set_backend_ip(ip: str):
    """Altera o IP do backend manualmente"""
    global _cached_backend_ip, BACKEND_IP
    _cached_backend_ip = ip
    BACKEND_IP = ip

def set_backend_port(port: int):
    """Altera a porta do backend manualmente"""
    global _cached_backend_port, BACKEND_PORT
    _cached_backend_port = port
    BACKEND_PORT = port

def clear_cache():
    """Limpa o cache de descoberta"""
    global _cached_backend_ip, _cached_backend_port
    _cached_backend_ip = None
    _cached_backend_port = None

if __name__ == "__main__":
    print("🔧 Testando configuração do backend...")
    print("="*50)
    print(f"Auto-discovery: {'✅ Ativado' if _auto_discovery_enabled else '❌ Desativado'}")
    print(f"Backend IP: {get_backend_ip()}")
    print(f"Backend Port: {get_backend_port()}")
    print(f"Backend URL: {get_backend_url()}")