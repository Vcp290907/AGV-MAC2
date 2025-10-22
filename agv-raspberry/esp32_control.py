#!/usr/bin/env python3
"""
Módulo de Controle dos ESP32 - Motores e Garra
Gerencia comunicação serial com dois ESP32: um para motores/buzzer, outro para garra
"""
import serial
import serial.tools.list_ports
import json
import time
import logging
from typing import Optional, Dict, Any
from config import (
    get_esp32_motor_port, get_esp32_motor_baudrate, get_esp32_motor_timeout,
    get_esp32_garra_port, get_esp32_garra_baudrate, get_esp32_garra_timeout
)

logger = logging.getLogger(__name__)

class ESP32Controller:
    """Controlador para comunicação com um ESP32 via serial"""

    def __init__(self, port: str, baudrate: int, timeout: float, name: str = "ESP32"):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.name = name
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        logger.info(f"{self.name} Controller inicializado - Porta: {self.port}, Baudrate: {self.baudrate}")

    def _auto_detect_port(self) -> Optional[str]:
        """Tenta detectar automaticamente a porta do ESP32"""
        logger.info(f"🔍 Procurando {self.name} automaticamente...")
        ports = serial.tools.list_ports.comports()
        usb_ports = [port.device for port in ports if 'USB' in port.device or 'ACM' in port.device]
        for port in usb_ports:
            if self._test_port(port):
                logger.info(f"✅ {self.name} encontrado na porta {port}")
                return port
        common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyUSB0', '/dev/ttyUSB1']
        for port in common_ports:
            if self._test_port(port):
                logger.info(f"✅ {self.name} encontrado na porta {port}")
                return port
        logger.warning(f"❌ {self.name} não encontrado automaticamente")
        return None

    def _test_port(self, port: str) -> bool:
        """Testa se uma porta específica tem o ESP32"""
        try:
            with serial.Serial(port, self.baudrate, timeout=self.timeout) as ser:
                ser.write(b'{"comando":"status"}\n')  # MUDADO: de "ping" para "status"
                time.sleep(0.5)
                response = self.serial_connection.readline().decode('utf-8').strip()
                if response and ('status' in response or 'OK' in response):  # MUDADO: verifica "status" ou "OK"
                    return True
        except (serial.SerialException, OSError):
            pass
        return False

    def connect(self) -> bool:
        """Estabelece conexão serial com ESP32"""
        try:
            if not self.port:
                self.port = self._auto_detect_port()
                if not self.port:
                    logger.error(f"❌ Não foi possível detectar porta para {self.name}")
                    return False
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.connected = True
            logger.info(f"✅ Conectado ao {self.name} na porta {self.port}")
            return self._test_connection()
        except serial.SerialException as e:
            logger.error(f"❌ Erro ao conectar {self.name}: {e}")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao conectar {self.name}: {e}")
            self.connected = False
        return False

    def disconnect(self):
        """Desconecta do ESP32"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.connected = False
            logger.info(f"🔌 Desconectado do {self.name}")

    def _test_connection(self) -> bool:
        """Testa se a conexão com ESP32 está funcionando"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return False
            self.serial_connection.write(b'{"comando":"status"}\n')  # MUDADO: de "ping" para "status"
            time.sleep(0.5)
            response = self.serial_connection.readline().decode('utf-8').strip()
            if response and ('status' in response or 'OK' in response):
                logger.info(f"✅ {self.name} responde: {response}")
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao testar {self.name}: {e}")
        return False

    def _send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Envia comando para ESP32 e aguarda resposta"""
        if not self.connected or not self.serial_connection:
            logger.error(f"❌ {self.name} não conectado")
            return None
        try:
            cmd_str = json.dumps(command) + '\n'
            self.serial_connection.write(cmd_str.encode('utf-8'))
            logger.debug(f"📤 Enviado para {self.name}: {cmd_str.strip()}")
            time.sleep(0.1)  # Pequena pausa para resposta
            response_line = self.serial_connection.readline().decode('utf-8').strip()
            if response_line:
                logger.debug(f"📥 Resposta de {self.name}: {response_line}")
                try:
                    return json.loads(response_line)
                except json.JSONDecodeError:
                    return {"raw_response": response_line}
        except serial.SerialTimeoutException:
            logger.error(f"⏰ Timeout ao enviar comando para {self.name}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar comando para {self.name}: {e}")
        return None

    def move_forward(self, duration: float = 1.0) -> Dict[str, Any]:
        """Move para frente (apenas para ESP32 Motor)"""
        if self.name != "ESP32 Motor":
            return {"success": False, "message": "Comando de movimento apenas para ESP32 Motor"}
        command = {"comando": "mover_frente", "velocidade": 50}
        response = self._send_command(command)
        if response and response.get("status") == "success":
            time.sleep(duration)
            self._send_command({"comando": "parar"})
            return {"success": True, "message": f"Movimento para frente por {duration}s"}
        return {"success": False, "message": "Falha no movimento"}

    def move_backward(self, duration: float = 1.0) -> Dict[str, Any]:
        """Move para trás (apenas para ESP32 Motor)"""
        if self.name != "ESP32 Motor":
            return {"success": False, "message": "Comando de movimento apenas para ESP32 Motor"}
        command = {"comando": "mover_tras", "velocidade": 50}
        response = self._send_command(command)
        if response and response.get("status") == "success":
            time.sleep(duration)
            self._send_command({"comando": "parar"})
            return {"success": True, "message": f"Movimento para trás por {duration}s"}
        return {"success": False, "message": "Falha no movimento"}

    def stop(self) -> Dict[str, Any]:
        """Para motores (apenas para ESP32 Motor)"""
        if self.name != "ESP32 Motor":
            return {"success": False, "message": "Comando de parada apenas para ESP32 Motor"}
        response = self._send_command({"comando": "parar"})
        return {"success": True} if response else {"success": False}

    def move_servos(self, angles: Dict[str, int]) -> Dict[str, Any]:
        """Move servos da garra (apenas para ESP32 Garra)"""
        if self.name != "ESP32 Garra":
            return {"success": False, "message": "Comando de servos apenas para ESP32 Garra"}
        command = {"comando": "move_servos", "angles": angles}
        response = self._send_command(command)
        return {"success": True} if response and response.get("status") == "success" else {"success": False}

    def executar_sequencia_garra(self, steps: list, repeats: int = 1) -> Dict[str, Any]:
        """Executa sequência da garra (apenas para ESP32 Garra)"""
        if self.name != "ESP32 Garra":
            return {"success": False, "message": "Comando de sequência apenas para ESP32 Garra"}
        command = {"comando": "sequencia_garra", "steps": steps, "repeats": repeats}
        response = self._send_command(command)
        return {"success": True} if response and response.get("status") == "success" else {"success": False}

    def get_status(self) -> Dict[str, Any]:
        """Obtém status"""
        response = self._send_command({"comando": "status"})
        return {"success": True, "status": response} if response else {"success": False}

# Instâncias globais para os dois ESP32
esp32_motor = ESP32Controller(
    port=get_esp32_motor_port(),
    baudrate=get_esp32_motor_baudrate(),
    timeout=get_esp32_motor_timeout(),
    name="ESP32 Motor"
)

esp32_garra = ESP32Controller(
    port=get_esp32_garra_port(),
    baudrate=get_esp32_garra_baudrate(),
    timeout=get_esp32_garra_timeout(),
    name="ESP32 Garra"
)

def get_esp32_motor_controller() -> ESP32Controller:
    """Retorna controlador do ESP32 de motores"""
    return esp32_motor

def get_esp32_garra_controller() -> ESP32Controller:
    """Retorna controlador do ESP32 de garra"""
    return esp32_garra

# Funções de conveniência para motores (roteiam para esp32_motor)
def connect_esp32_motor(port: str = None, baudrate: int = None, timeout: float = None) -> bool:
    """Conecta ao ESP32 de motores"""
    controller = get_esp32_motor_controller()
    if port:
        controller.port = port
    if baudrate:
        controller.baudrate = baudrate
    if timeout:
        controller.timeout = timeout
    return controller.connect()

def move_forward_esp32(duration: float = 1.0) -> Dict[str, Any]:
    """Move para frente via ESP32 de motores"""
    return get_esp32_motor_controller().move_forward(duration)

def move_backward_esp32(duration: float = 1.0) -> Dict[str, Any]:
    """Move para trás via ESP32 de motores"""
    return get_esp32_motor_controller().move_backward(duration)

def stop_esp32() -> Dict[str, Any]:
    """Para movimento via ESP32 de motores"""
    return get_esp32_motor_controller().stop()

def get_status_motor() -> Dict[str, Any]:
    """Obtém status do ESP32 de motores"""
    return get_esp32_motor_controller().get_status()

# Funções de conveniência para garra (roteiam para esp32_garra)
def connect_esp32_garra(port: str = None, baudrate: int = None, timeout: float = None) -> bool:
    """Conecta ao ESP32 de garra"""
    controller = get_esp32_garra_controller()
    if port:
        controller.port = port
    if baudrate:
        controller.baudrate = baudrate
    if timeout:
        controller.timeout = timeout
    return controller.connect()

def move_servos_esp32(angles: Dict[str, int]) -> Dict[str, Any]:
    """Move servos da garra via ESP32 de garra - mapeia chaves para firmware"""
    # Mapeia chaves Python para chaves do firmware ESPcima.ino
    cmd = {"comando": "move_servos"}
    if "giro" in angles:
        cmd["a"] = angles["giro"]  # motorGiroGarra
    if "um" in angles:
        cmd["b"] = angles["um"]    # motorUm
    if "dois" in angles:
        cmd["c"] = angles["dois"]  # motorDois
    if "garra" in angles:
        cmd["d"] = angles["garra"] # motorGarra
    if "servo3" in angles:
        cmd["e"] = angles["servo3"] # motorTres
    
    return get_esp32_garra_controller()._send_command(cmd)

def executar_sequencia_garra(steps: list, repeats: int = 1) -> Dict[str, Any]:
    """Executa sequência da garra via ESP32 de garra"""
    return get_esp32_garra_controller().executar_sequencia_garra(steps, repeats)

def get_status_garra() -> Dict[str, Any]:
    """Obtém status do ESP32 de garra"""
    return get_esp32_garra_controller().get_status()

if __name__ == "__main__":
    # Teste do módulo
    print("🧪 Testando comunicação com ESP32 Motor e Garra...")

    if connect_esp32_motor():
        print("✅ ESP32 Motor conectado")
        status = get_status_motor()
        print(f"Status Motor: {status}")
    else:
        print("❌ Falha ao conectar ESP32 Motor")

    if connect_esp32_garra():
        print("✅ ESP32 Garra conectado")
        status = get_status_garra()
        print(f"Status Garra: {status}")
    else:
        print("❌ Falha ao conectar ESP32 Garra")