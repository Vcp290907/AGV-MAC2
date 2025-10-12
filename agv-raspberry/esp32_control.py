#!/usr/bin/env python3
"""
Módulo de Controle do ESP32 - Servo Motores
Gerencia comunicação serial com ESP32 para controle de servo motores
"""

import serial
import time
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ESP32Controller:
    """Controlador para comunicação com ESP32 via serial"""

    def __init__(self, port: str = None, baudrate: int = 115200, timeout: float = 2.0):
        self.default_port = port or '/dev/ttyACM0'  # Mudado para ttyACM0 baseado na detecção
        self.port = self.default_port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False

        logger.info(f"ESP32 Controller inicializado - Porta: {self.port}, Baudrate: {baudrate}")

    def _auto_detect_port(self) -> Optional[str]:
        """Tenta detectar automaticamente a porta do ESP32"""
        import serial.tools.list_ports

        logger.info("🔍 Procurando ESP32 automaticamente...")

        ports = serial.tools.list_ports.comports()
        usb_ports = [port.device for port in ports if 'USB' in port.device or 'ACM' in port.device]

        for port in usb_ports:
            logger.debug(f"Testando porta: {port}")
            try:
                # Tentar conectar rapidamente
                test_serial = serial.Serial(port, self.baudrate, timeout=1)

                # Enviar ping
                ping_cmd = {'comando': 'ping', 'timestamp': time.time()}
                test_serial.write((json.dumps(ping_cmd) + '\n').encode('utf-8'))
                test_serial.flush()

                # Aguardar resposta
                response = test_serial.readline().decode('utf-8').strip()
                test_serial.close()

                if response:
                    try:
                        response_data = json.loads(response)
                        if response_data.get('status') in ['ok', 'success']:
                            logger.info(f"✅ ESP32 encontrado na porta: {port}")
                            return port
                    except json.JSONDecodeError:
                        pass

            except (serial.SerialException, OSError):
                continue

        logger.warning("❌ ESP32 não encontrado automaticamente")
        return None

    def connect(self) -> bool:
        """Estabelece conexão serial com ESP32"""
        try:
            # Se porta foi especificada explicitamente, não fazer auto-detecção
            if self.port != self.default_port:
                # Porta específica fornecida - tentar conectar diretamente
                try:
                    self.serial_connection = serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        timeout=self.timeout,
                        write_timeout=self.timeout
                    )
                except (serial.SerialException, OSError) as e:
                    logger.error(f"❌ Porta especificada {self.port} não disponível: {e}")
                    return False
            else:
                # Porta padrão - tentar auto-detecção
                try:
                    self.serial_connection = serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        timeout=self.timeout,
                        write_timeout=self.timeout
                    )
                except (serial.SerialException, OSError) as e:
                    logger.warning(f"❌ Porta padrão {self.port} não disponível: {e}")

                    # Tentar auto-detecção
                    auto_port = self._auto_detect_port()
                    if auto_port:
                        logger.info(f"🔄 Tentando porta detectada automaticamente: {auto_port}")
                        self.port = auto_port
                        self.serial_connection = serial.Serial(
                            port=self.port,
                            baudrate=self.baudrate,
                            timeout=self.timeout,
                            write_timeout=self.timeout
                        )
                    else:
                        logger.error("❌ ESP32 não encontrado em nenhuma porta")
                        return False

            # Limpar buffer serial e aguardar estabilização
            time.sleep(2)  # Mesmo tempo que debug_serial.py usa
            if self.serial_connection.in_waiting > 0:
                self.serial_connection.read(self.serial_connection.in_waiting)

            # Testar conexão enviando comando de status
            if self._test_connection():
                self.connected = True
                logger.info(f"✅ Conectado ao ESP32 na porta {self.port}")
                return True
            else:
                logger.warning(f"❌ ESP32 não respondeu na porta {self.port}")
                self.serial_connection.close()
                return False

        except serial.SerialException as e:
            logger.error(f"❌ Erro ao conectar na porta {self.port}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado na conexão: {e}")
            return False

    def disconnect(self):
        """Desconecta do ESP32"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.connected = False
            logger.info("🔌 Desconectado do ESP32")

    def _test_connection(self) -> bool:
        """Testa se a conexão com ESP32 está funcionando"""
        try:
            # Aguardar ESP32 estabilizar
            time.sleep(2)

            # Enviar comando de teste simples (igual ao debug_serial.py)
            test_command = {'comando': 'ping'}
            command_json = json.dumps(test_command) + '\n'

            # Enviar comando
            self.serial_connection.write(command_json.encode('utf-8'))
            self.serial_connection.flush()

            # Aguardar resposta
            response_line = self.serial_connection.readline().decode('utf-8').strip()

            if response_line:
                try:
                    response = json.loads(response_line)
                    if response.get('status') == 'ok':
                        return True
                except json.JSONDecodeError:
                    pass

            return False

        except Exception as e:
            logger.debug(f"Erro no teste de conexão: {e}")
            return False

    def _send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Envia comando para ESP32 e aguarda resposta"""
        if not self.connected or not self.serial_connection:
            logger.error("ESP32 não está conectado")
            return None

        try:
            # Converter comando para JSON
            command_json = json.dumps(command) + '\n'

            # Enviar comando
            self.serial_connection.write(command_json.encode('utf-8'))
            self.serial_connection.flush()

            logger.debug(f"📤 Comando enviado: {command}")

            # Aguardar resposta
            response_line = self.serial_connection.readline().decode('utf-8').strip()

            if response_line:
                try:
                    response = json.loads(response_line)
                    logger.debug(f"📥 Resposta recebida: {response}")
                    return response
                except json.JSONDecodeError as e:
                    logger.warning(f"Resposta inválida do ESP32: {response_line} - {e}")
                    return None
            else:
                logger.warning("Nenhuma resposta recebida do ESP32")
                return None

        except serial.SerialTimeoutException:
            logger.error("Timeout na comunicação serial")
            return None
        except Exception as e:
            logger.error(f"Erro na comunicação serial: {e}")
            return None

    def move_forward(self, duration: float = 1.0) -> Dict[str, Any]:
        """Move o AGV para frente por determinado tempo"""
        command = {
            'comando': 'move',
            'direction': 'forward',
            'duration': duration,
            'timestamp': time.time()
        }

        logger.info(f"🚗 Movendo para frente por {duration}s")

        response = self._send_command(command)

        if response and response.get('status') == 'success':
            logger.info("✅ Movimento para frente concluído")
            return {
                'success': True,
                'message': f'Movimento para frente executado por {duration} segundos',
                'direction': 'forward',
                'duration': duration
            }
        else:
            error_msg = response.get('error', 'Erro desconhecido') if response else 'Sem resposta'
            logger.error(f"❌ Falha no movimento para frente: {error_msg}")
            return {
                'success': False,
                'message': f'Falha no movimento para frente: {error_msg}',
                'direction': 'forward',
                'duration': duration
            }

    def move_backward(self, duration: float = 1.0) -> Dict[str, Any]:
        """Move o AGV para trás por determinado tempo"""
        command = {
            'comando': 'move',
            'direction': 'backward',
            'duration': duration,
            'timestamp': time.time()
        }

        logger.info(f"🚗 Movendo para trás por {duration}s")

        response = self._send_command(command)

        if response and response.get('status') == 'success':
            logger.info("✅ Movimento para trás concluído")
            return {
                'success': True,
                'message': f'Movimento para trás executado por {duration} segundos',
                'direction': 'backward',
                'duration': duration
            }
        else:
            error_msg = response.get('error', 'Erro desconhecido') if response else 'Sem resposta'
            logger.error(f"❌ Falha no movimento para trás: {error_msg}")
            return {
                'success': False,
                'message': f'Falha no movimento para trás: {error_msg}',
                'direction': 'backward',
                'duration': duration
            }

    def stop(self) -> Dict[str, Any]:
        """Para imediatamente o movimento do AGV"""
        command = {
            'comando': 'stop',
            'timestamp': time.time()
        }

        logger.info("🛑 Parando movimento")

        response = self._send_command(command)

        if response and response.get('status') == 'success':
            logger.info("✅ Movimento parado")
            return {
                'success': True,
                'message': 'Movimento parado com sucesso'
            }
        else:
            error_msg = response.get('error', 'Erro desconhecido') if response else 'Sem resposta'
            logger.error(f"❌ Falha ao parar movimento: {error_msg}")
            return {
                'success': False,
                'message': f'Falha ao parar movimento: {error_msg}'
            }

    def get_status(self) -> Dict[str, Any]:
        """Obtém status do ESP32"""
        command = {
            'comando': 'status',
            'timestamp': time.time()
        }

        response = self._send_command(command)

        if response:
            return {
                'success': True,
                'status': response
            }
        else:
            return {
                'success': False,
                'message': 'Falha ao obter status do ESP32'
            }

    def set_speed(self, speed: int) -> Dict[str, Any]:
        """Define velocidade dos motores (não suportado para servo motores)"""
        logger.warning("⚠️ Controle de velocidade não disponível para servo motores")

        return {
            'success': True,  # Retorna sucesso para compatibilidade
            'message': 'Controle de velocidade não disponível para servo motores',
            'note': 'Servo motors operate at fixed speed'
        }

# Instância global do controlador
esp32_controller = ESP32Controller()

def get_esp32_controller() -> ESP32Controller:
    """Retorna instância global do controlador ESP32"""
    return esp32_controller

# Funções de conveniência para uso direto
def connect_esp32(port: str = '/dev/ttyACM0') -> bool:
    """Conecta ao ESP32"""
    controller = get_esp32_controller()
    controller.port = port
    return controller.connect()

def move_forward_esp32(duration: float = 1.0) -> Dict[str, Any]:
    """Move para frente via ESP32"""
    return get_esp32_controller().move_forward(duration)

def move_backward_esp32(duration: float = 1.0) -> Dict[str, Any]:
    """Move para trás via ESP32"""
    return get_esp32_controller().move_backward(duration)

def stop_esp32() -> Dict[str, Any]:
    """Para movimento via ESP32"""
    return get_esp32_controller().stop()

if __name__ == "__main__":
    # Teste do módulo
    print("🧪 Testando comunicação com ESP32...")

    if connect_esp32():
        print("✅ Conectado ao ESP32!")

        # Teste movimento para frente
        result = move_forward_esp32(0.5)
        print(f"Frente: {result}")

        time.sleep(1)

        # Teste movimento para trás
        result = move_backward_esp32(0.5)
        print(f"Trás: {result}")

        # Desconectar
        get_esp32_controller().disconnect()
        print("🔌 Desconectado")
    else:
        print("❌ Falha na conexão com ESP32")