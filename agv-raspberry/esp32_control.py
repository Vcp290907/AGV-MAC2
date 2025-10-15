#!/usr/bin/env python3
"""
Módulo de Controle do ESP32 - Comunicação com ESP32

Suporta dois protocolos:
- Protocolo JSON (existente): comandos como {'comando': 'move', ...}
- Protocolo texto para garra/servos: "MOVE a b c d e", "STATUS", "RUNSEQ"

Assim podemos integrar um firmware de garra que já funciona com comandos de linha
sem quebrar o restante do sistema que usa JSON.
"""

import serial
import time
import logging
import json
from typing import Optional, Dict, Any
from config import get_esp32_port, get_esp32_baudrate, get_esp32_timeout

logger = logging.getLogger(__name__)

class ESP32Controller:
    """Controlador para comunicação com ESP32 via serial"""

    def __init__(self, port: str = None, baudrate: int = None, timeout: float = None):
        # Usar configurações do arquivo config.py se não especificadas
        self.default_port = port or get_esp32_port()
        self.default_baudrate = baudrate or get_esp32_baudrate()
        self.default_timeout = timeout or get_esp32_timeout()
        
        self.port = self.default_port
        self.baudrate = self.default_baudrate
        self.timeout = self.default_timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False

        logger.info(f"ESP32 Controller inicializado - Porta: {self.port}, Baudrate: {self.baudrate}")

    def _auto_detect_port(self) -> Optional[str]:
        """Tenta detectar automaticamente a porta do ESP32"""
        import serial.tools.list_ports

        logger.info("🔍 Procurando ESP32 automaticamente...")

        ports = serial.tools.list_ports.comports()
        usb_ports = [port.device for port in ports if 'USB' in port.device or 'ACM' in port.device]

        # Tentar portas detectadas
        for port in usb_ports:
            logger.debug(f"Testando porta: {port}")
            if self._test_port(port):
                return port

        # Se não encontrou, tentar portas comuns
        common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyUSB0', '/dev/ttyUSB1']
        for port in common_ports:
            logger.debug(f"Testando porta comum: {port}")
            if self._test_port(port):
                return port

        logger.warning("❌ ESP32 não encontrado automaticamente")
        return None

    def _test_port(self, port: str) -> bool:
        """Testa se uma porta específica tem o ESP32"""
        try:
            # Tentar conectar rapidamente
            test_serial = serial.Serial(port, self.baudrate, timeout=1)

            # Enviar ping (JSON)
            ping_cmd = {'comando': 'ping', 'timestamp': time.time()}
            test_serial.write((json.dumps(ping_cmd) + '\n').encode('utf-8'))
            test_serial.flush()

            # Aguardar resposta
            response = test_serial.readline().decode('utf-8').strip()
            if response:
                # Aceitar tanto JSON quanto resposta simples
                if response.strip() in ['OK', 'ok', 'success', 'pong']:
                    test_serial.close()
                    return True
                try:
                    response_data = json.loads(response)
                    if response_data.get('status') in ['ok', 'success'] or response_data.get('resposta') == 'pong':
                        test_serial.close()
                        return True
                except json.JSONDecodeError:
                    pass

            # Fallback: tentar protocolo de texto da garra
            try:
                test_serial.write(b'STATUS\n')
                test_serial.flush()
                time.sleep(0.05)
                lines = []
                for _ in range(5):
                    ln = test_serial.readline().decode('utf-8', errors='ignore').strip()
                    if not ln:
                        break
                    lines.append(ln)
                # Heurística: presença de "giro:" e/ou "OK"
                if any(ln.lower() == 'ok' for ln in lines) or any('giro:' in ln for ln in lines):
                    test_serial.close()
                    return True
            except Exception:
                pass

            test_serial.close()

        except (serial.SerialException, OSError):
            pass

        return False

    def connect(self) -> bool:
        """Estabelece conexão serial com ESP32"""
        try:
            # Sempre tentar auto-detecção primeiro
            logger.info("🔍 Tentando detectar ESP32 automaticamente...")
            auto_port = self._auto_detect_port()
            if auto_port:
                logger.info(f"✅ ESP32 detectado na porta: {auto_port}")
                self.port = auto_port
            else:
                logger.warning("❌ ESP32 não detectado automaticamente, tentando porta padrão...")

            # Tentar conectar na porta detectada ou padrão
            try:
                self.serial_connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.timeout
                )
            except (serial.SerialException, OSError) as e:
                logger.error(f"❌ Porta {self.port} não disponível: {e}")
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

            # Enviar comando de teste (JSON)
            test_command = {'comando': 'ping'}
            command_json = json.dumps(test_command) + '\n'

            # Enviar comando
            self.serial_connection.write(command_json.encode('utf-8'))
            self.serial_connection.flush()

            # Aguardar resposta
            response_line = self.serial_connection.readline().decode('utf-8').strip()

            if response_line:
                # Aceitar tanto JSON quanto resposta simples
                if response_line.strip() in ['OK', 'ok', 'success', 'pong']:
                    return True
                
                try:
                    response = json.loads(response_line)
                    if response.get('status') == 'ok':
                        return True
                except json.JSONDecodeError:
                    pass

            # Fallback: testar protocolo texto (garra)
            try:
                self.serial_connection.write(b'STATUS\n')
                self.serial_connection.flush()
                time.sleep(0.05)
                lines = []
                for _ in range(5):
                    ln = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if not ln:
                        break
                    lines.append(ln)
                if any(ln.lower() == 'ok' for ln in lines) or any('giro:' in ln for ln in lines):
                    return True
            except Exception:
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

            # Ler múltiplas respostas possíveis (ESP32 pode enviar debug + status)
            responses = []
            for _ in range(3):  # Máximo 3 respostas
                try:
                    response_line = self.serial_connection.readline().decode('utf-8').strip()
                    if response_line:
                        responses.append(response_line)
                    else:
                        break
                except:
                    break
                time.sleep(0.05)  # Pequena pausa entre leituras

            # Processar respostas
            for response_line in responses:
                # Aceitar tanto JSON quanto resposta simples
                if response_line.strip() in ['OK', 'ok', 'success']:
                    logger.debug(f"📥 Resposta simples recebida: {response_line}")
                    return {'status': 'ok', 'resposta': response_line.strip()}
                
                try:
                    response = json.loads(response_line)
                    logger.debug(f"📥 Resposta JSON recebida: {response}")
                    # Aceitar qualquer resposta JSON com status de sucesso
                    if response.get('status') in ['success', 'ok']:
                        return response
                    # Ou resposta com informações dos motores (debug)
                    if 'motores' in response:
                        return response
                except json.JSONDecodeError as e:
                    logger.warning(f"Resposta simples do ESP32: {response_line} - {e}")
                    # Retornar resposta simples como sucesso
                    return {'status': 'ok', 'resposta': response_line.strip()}

            # Se chegou aqui, não encontrou resposta válida
            logger.warning("Nenhuma resposta válida recebida do ESP32")
            return None

        except serial.SerialTimeoutException:
            logger.error("Timeout na comunicação serial")
            return None
        except Exception as e:
            logger.error(f"Erro na comunicação serial: {e}")
            return None

    # =========================
    # Protocolo texto - Garra
    # =========================
    def _send_line(self, line: str, max_lines: int = 6, read_pause: float = 0.03) -> Optional[list]:
        """Envia uma linha plain-text e retorna as linhas de resposta (ou None em erro)."""
        if not self.connected or not self.serial_connection:
            logger.error("ESP32 não está conectado")
            return None
        try:
            if not line.endswith('\n'):
                line_to_send = line + '\n'
            else:
                line_to_send = line
            self.serial_connection.write(line_to_send.encode('utf-8'))
            self.serial_connection.flush()
            time.sleep(read_pause)
            lines = []
            for _ in range(max_lines):
                try:
                    ln = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if not ln:
                        break
                    lines.append(ln)
                except Exception:
                    break
            logger.debug(f"📥 Resposta texto: {lines}")
            return lines
        except Exception as e:
            logger.error(f"Erro ao enviar linha: {e}")
            return None

    def arm_move(self, giro: int, um: int, dois: int, garra: int, tres: int) -> Dict[str, Any]:
        """Move a garra/servos com comando texto: MOVE a b c d e"""
        cmd = f"MOVE {int(giro)} {int(um)} {int(dois)} {int(garra)} {int(tres)}"
        logger.info(f"🦾 Enviando comando de garra: {cmd}")
        lines = self._send_line(cmd)
        ok = bool(lines) and any(l.strip().lower() == 'ok' for l in lines)
        return {'success': ok, 'raw': lines or []}

    def arm_status(self) -> Dict[str, Any]:
        """Consulta STATUS dos servos (espera linhas com angulos + 'OK')."""
        lines = self._send_line('STATUS')
        if not lines:
            return {'success': False, 'message': 'Sem resposta'}
        # Tentar extrair leituras
        status = {'raw': lines}
        try:
            for ln in lines:
                low = ln.lower()
                if 'giro:' in low:
                    # Exemplo: "giro:30 um:160 dois:170 garra:73"
                    parts = low.replace('\t', ' ').split()
                    for p in parts:
                        if ':' in p:
                            k, v = p.split(':', 1)
                            try:
                                status[k] = int(float(v))
                            except Exception:
                                pass
        except Exception:
            pass
        status['success'] = any(l.strip().lower() == 'ok' for l in lines)
        return status

    def arm_run_sequence(self) -> Dict[str, Any]:
        """Roda a sequência interna do firmware (RUNSEQ ou 'x')."""
        # Preferir RUNSEQ se suportado
        lines = self._send_line('RUNSEQ')
        if not lines or all('ERR' in l for l in lines):
            lines = self._send_line('x')
        ok = bool(lines) and any(l.strip().lower() == 'ok' for l in lines)
        return {'success': ok, 'raw': lines or []}

    def move_forward(self, duration: float = 1.0) -> Dict[str, Any]:
        """Move o AGV para frente por determinado tempo"""
        command = {
            'comando': 'move',
            'direction': 'forward',
            'duration': duration,
            'timestamp': time.time()
        }

        logger.info(f"🚗 Movendo para frente por {duration}s")

        # Enviar comando de movimento
        response = self._send_command(command)

        if response and response.get('status') in ['success', 'ok']:
            # Aguardar a duração especificada
            time.sleep(duration)
            
            # Parar os motores após a duração
            stop_response = self._send_command({'comando': 'stop', 'timestamp': time.time()})
            
            if stop_response and (stop_response.get('status') in ['success', 'ok'] or 'motores' in stop_response):
                logger.info("✅ Movimento para frente concluído e parado")
                return {
                    'success': True,
                    'message': f'Movimento para frente executado por {duration} segundos',
                    'direction': 'forward',
                    'duration': duration
                }
            else:
                logger.warning("Movimento executado mas falha ao parar")
                return {
                    'success': True,  # Movimento foi executado mesmo sem parar corretamente
                    'message': f'Movimento para frente executado por {duration} segundos (aviso: pode não ter parado)',
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

        # Enviar comando de movimento
        response = self._send_command(command)

        if response and response.get('status') in ['success', 'ok']:
            # Aguardar a duração especificada
            time.sleep(duration)
            
            # Parar os motores após a duração
            stop_response = self._send_command({'comando': 'stop', 'timestamp': time.time()})
            
            if stop_response and (stop_response.get('status') in ['success', 'ok'] or 'motores' in stop_response):
                logger.info("✅ Movimento para trás concluído e parado")
                return {
                    'success': True,
                    'message': f'Movimento para trás executado por {duration} segundos',
                    'direction': 'backward',
                    'duration': duration
                }
            else:
                logger.warning("Movimento executado mas falha ao parar")
                return {
                    'success': True,  # Movimento foi executado mesmo sem parar corretamente
                    'message': f'Movimento para trás executado por {duration} segundos (aviso: pode não ter parado)',
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

        if response and response.get('status') in ['success', 'ok']:
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
def connect_esp32(port: str = None, baudrate: int = None, timeout: float = None) -> bool:
    """Conecta ao ESP32 usando configurações do config.py se não especificadas"""
    controller = get_esp32_controller()
    if port:
        controller.port = port
    if baudrate:
        controller.baudrate = baudrate
    if timeout:
        controller.timeout = timeout
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