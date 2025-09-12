#!/usr/bin/env python3
"""
Módulo de Comunicação WiFi
Gerencia conexão e comunicação entre PC e Raspberry Pi
"""

import socket
import json
import logging
import time
from datetime import datetime
import asyncio
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WiFiCommunication:
    """Gerencia comunicação WiFi com o sistema PC"""

    def __init__(self, agv_system, pc_ip: str = None, pc_port: int = 5000):
        self.agv_system = agv_system
        self.pc_ip = pc_ip or self._discover_pc_ip()
        self.pc_port = pc_port
        self.connected = False
        self.last_heartbeat = None
        self.connection_attempts = 0
        self.max_connection_attempts = 10

        # Configurações de rede
        self.local_ip = self._get_local_ip()
        self.local_port = 8080

        logger.info(f"Comunicação WiFi inicializada - PC: {self.pc_ip}:{self.pc_port}")

    def _get_local_ip(self) -> str:
        """Obtém IP local do Raspberry Pi"""
        try:
            # Criar socket temporário para descobrir IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Conectar a um servidor externo
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            logger.warning(f"Erro ao obter IP local: {e}")
            return "127.0.0.1"

    def _discover_pc_ip(self) -> str:
        """Descobre IP do PC na rede local"""
        logger.info("Descobrindo IP do PC...")

        # IPs comuns para tentar
        common_ips = [
            "192.168.0.100", "192.168.0.101", "192.168.0.102",
            "192.168.1.100", "192.168.1.101", "192.168.1.102",
            "10.0.0.100", "10.0.0.101", "10.0.0.102"
        ]

        for ip in common_ips:
            if self._test_pc_connection(ip):
                logger.info(f"PC encontrado em: {ip}")
                return ip

        logger.warning("PC não encontrado automaticamente, usando IP padrão")
        return "192.168.0.100"  # IP padrão

    def _test_pc_connection(self, ip: str) -> bool:
        """Testa conexão com PC"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, self.pc_port))
            sock.close()

            if result == 0:
                # Testar se é realmente o servidor AGV
                try:
                    response = self._make_request(ip, "/test", timeout=3)
                    if response and response.get('message') == 'AGV System API':
                        return True
                except:
                    pass

            return False
        except Exception as e:
            logger.debug(f"Erro ao testar conexão com {ip}: {e}")
            return False

    def _make_request(self, ip: str, endpoint: str, method: str = "GET",
                     data: Dict = None, timeout: int = 5) -> Optional[Dict]:
        """Faz requisição HTTP para o PC"""
        try:
            import urllib.request
            import urllib.parse

            url = f"http://{ip}:{self.pc_port}{endpoint}"

            if method == "GET":
                req = urllib.request.Request(url)
            else:
                req = urllib.request.Request(url, method=method)
                if data:
                    req.add_header('Content-Type', 'application/json')
                    data_json = json.dumps(data).encode('utf-8')
                    req.data = data_json

            req.add_header('User-Agent', 'AGV-RaspberryPi/1.0')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return response_data

        except Exception as e:
            logger.debug(f"Erro na requisição {method} {endpoint}: {e}")
            return None

    async def connect_to_pc(self) -> bool:
        """Estabelece conexão com o PC"""
        logger.info("Tentando conectar ao PC...")

        if self.connection_attempts >= self.max_connection_attempts:
            logger.warning("Máximo de tentativas de conexão atingido")
            return False

        self.connection_attempts += 1

        # Testar conexão
        if self._test_pc_connection(self.pc_ip):
            self.connected = True
            self.last_heartbeat = datetime.now()
            self.connection_attempts = 0

            logger.info(f"Conectado ao PC: {self.pc_ip}:{self.pc_port}")

            # Registrar Raspberry Pi no PC
            await self._register_with_pc()

            return True
        else:
            logger.warning(f"Falha ao conectar ao PC (tentativa {self.connection_attempts})")
            return False

    async def _register_with_pc(self):
        """Registra Raspberry Pi no sistema PC"""
        try:
            registration_data = {
                'type': 'raspberry_registration',
                'ip': self.local_ip,
                'port': self.local_port,
                'status': self.agv_system.get_status(),
                'timestamp': datetime.now().isoformat()
            }

            response = self._make_request(self.pc_ip, "/agv/register", "POST", registration_data)

            if response and response.get('success'):
                logger.info("Raspberry Pi registrado com sucesso no PC")
            else:
                logger.warning("Falha ao registrar Raspberry Pi no PC")

        except Exception as e:
            logger.error(f"Erro ao registrar Raspberry Pi: {e}")

    async def send_status_update(self):
        """Envia atualização de status para o PC"""
        if not self.connected:
            return

        try:
            status_data = {
                'type': 'status_update',
                'agv_id': 'AGV_01',
                'status': self.agv_system.get_status(),
                'timestamp': datetime.now().isoformat()
            }

            response = self._make_request(self.pc_ip, "/agv/status", "POST", status_data)

            if response and response.get('success'):
                self.last_heartbeat = datetime.now()
                logger.debug("Status enviado com sucesso para PC")
            else:
                logger.warning("Falha ao enviar status para PC")

        except Exception as e:
            logger.error(f"Erro ao enviar status: {e}")
            self.connected = False

    async def send_command_acknowledgment(self, command_id: str, success: bool, result: Dict = None):
        """Envia confirmação de execução de comando"""
        if not self.connected:
            return

        try:
            ack_data = {
                'command_id': command_id,
                'success': success,
                'result': result or {},
                'timestamp': datetime.now().isoformat()
            }

            response = self._make_request(self.pc_ip, "/agv/command_ack", "POST", ack_data)

            if response and response.get('success'):
                logger.info(f"Confirmação de comando {command_id} enviada")
            else:
                logger.warning(f"Falha ao enviar confirmação de comando {command_id}")

        except Exception as e:
            logger.error(f"Erro ao enviar confirmação: {e}")

    async def request_command_from_pc(self) -> Optional[Dict]:
        """Solicita próximo comando do PC"""
        if not self.connected:
            return None

        try:
            response = self._make_request(self.pc_ip, "/agv/next_command", "GET")

            if response and response.get('success') and response.get('command'):
                command = response['command']
                logger.info(f"Novo comando recebido: {command.get('type')}")
                return command
            else:
                return None

        except Exception as e:
            logger.error(f"Erro ao solicitar comando: {e}")
            return None

    async def sync_data_with_pc(self):
        """Sincroniza dados com o PC"""
        if not self.connected:
            return

        try:
            # Sincronizar pedidos ativos
            response = self._make_request(self.pc_ip, "/agv/sync_orders", "GET")

            if response and response.get('success'):
                orders = response.get('orders', [])
                logger.info(f"Sincronizados {len(orders)} pedidos com PC")

                # TODO: Processar pedidos sincronizados

        except Exception as e:
            logger.error(f"Erro na sincronização de dados: {e}")

    async def heartbeat_loop(self):
        """Loop de heartbeat para manter conexão ativa"""
        while self.agv_system.running:
            try:
                if self.connected:
                    # Verificar se heartbeat ainda é válido (últimos 30 segundos)
                    if self.last_heartbeat and (datetime.now() - self.last_heartbeat).seconds > 30:
                        logger.warning("Heartbeat expirado, reconectando...")
                        self.connected = False
                    else:
                        # Enviar heartbeat
                        await self.send_status_update()
                else:
                    # Tentar reconectar
                    await self.connect_to_pc()

                await asyncio.sleep(10)  # Heartbeat a cada 10 segundos

            except Exception as e:
                logger.error(f"Erro no heartbeat: {e}")
                self.connected = False
                await asyncio.sleep(5)

    async def command_polling_loop(self):
        """Loop para verificar novos comandos do PC"""
        while self.agv_system.running:
            try:
                if self.connected:
                    # Verificar se há novos comandos
                    command = await self.request_command_from_pc()

                    if command:
                        # Executar comando
                        result = await self.agv_system.execute_command(command)

                        # Enviar confirmação
                        await self.send_command_acknowledgment(
                            command.get('id', 'unknown'),
                            result.get('success', False),
                            result
                        )

                await asyncio.sleep(2)  # Verificar comandos a cada 2 segundos

            except Exception as e:
                logger.error(f"Erro no polling de comandos: {e}")
                await asyncio.sleep(5)

    async def data_sync_loop(self):
        """Loop de sincronização de dados"""
        while self.agv_system.running:
            try:
                if self.connected:
                    await self.sync_data_with_pc()

                await asyncio.sleep(60)  # Sincronizar a cada minuto

            except Exception as e:
                logger.error(f"Erro na sincronização: {e}")
                await asyncio.sleep(30)

    def get_connection_status(self) -> Dict[str, Any]:
        """Retorna status da conexão"""
        return {
            'connected': self.connected,
            'pc_ip': self.pc_ip,
            'pc_port': self.pc_port,
            'local_ip': self.local_ip,
            'local_port': self.local_port,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'connection_attempts': self.connection_attempts
        }

    async def disconnect(self):
        """Desconecta do PC"""
        try:
            if self.connected:
                # Enviar desconexão
                disconnect_data = {
                    'type': 'disconnect',
                    'timestamp': datetime.now().isoformat()
                }

                self._make_request(self.pc_ip, "/agv/disconnect", "POST", disconnect_data)

            self.connected = False
            logger.info("Desconectado do PC")

        except Exception as e:
            logger.error(f"Erro na desconexão: {e}")