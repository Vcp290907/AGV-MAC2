#!/usr/bin/env python3
"""
Sistema de Descoberta Automática dos ESP32
Identifica automaticamente qual ESP32 é o Motor e qual é a Garra
baseado em IDs de hardware ou respostas de identificação
"""

import serial
import serial.tools.list_ports
import time
import json
import logging
from typing import Optional, Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESP32Discovery:
    """Sistema de descoberta automática dos ESP32"""
    
    # Identificadores esperados (podem ser ajustados)
    MOTOR_IDENTIFIERS = [
        "ESP32_MOTOR",
        "MOTOR",
        "DRIVE",
        "WHEELS",
        "motor",
        "motores"
    ]
    
    GARRA_IDENTIFIERS = [
        "ESP32_GARRA",
        "GARRA",
        "GRIPPER",
        "ARM",
        "SERVO",
        "garra",
        "servos"
    ]
    
    def __init__(self, baudrate: int = 115200, timeout: float = 2.0):
        self.baudrate = baudrate
        self.timeout = timeout
        self.motor_port = None
        self.garra_port = None
        
    def list_available_ports(self) -> List[serial.tools.list_ports.ListPortInfo]:
        """Lista todas as portas seriais disponíveis"""
        ports = serial.tools.list_ports.comports()
        logger.info(f"🔍 Portas seriais encontradas: {len(ports)}")
        
        for port in ports:
            logger.info(f"   📌 {port.device}")
            logger.info(f"      Descrição: {port.description}")
            logger.info(f"      VID:PID: {port.vid}:{port.pid}")
            logger.info(f"      Serial Number: {port.serial_number}")
            
        return ports
    
    def identify_esp32(self, port: str) -> Optional[str]:
        """
        Tenta identificar qual ESP32 está conectado na porta
        
        Returns:
            'motor', 'garra' ou None
        """
        try:
            logger.info(f"🔍 Testando porta {port}...")
            
            with serial.Serial(port, self.baudrate, timeout=self.timeout) as ser:
                time.sleep(0.5)  # Aguardar estabilização
                
                # Limpar buffer
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # Método 1: Enviar comando de identificação
                commands = [
                    b'{"comando":"identify"}\n',
                    b'{"comando":"whoami"}\n',
                    b'{"comando":"id"}\n',
                    b'{"comando":"status"}\n',
                ]
                
                for cmd in commands:
                    try:
                        ser.write(cmd)
                        time.sleep(0.3)
                        
                        # Ler múltiplas linhas de resposta
                        for _ in range(5):
                            if ser.in_waiting > 0:
                                response = ser.readline().decode('utf-8', errors='ignore').strip()
                                
                                if response:
                                    logger.info(f"   📥 Resposta: {response}")
                                    
                                    response_lower = response.lower()
                                    
                                    # Verificar identificadores de motor
                                    for identifier in self.MOTOR_IDENTIFIERS:
                                        if identifier.lower() in response_lower:
                                            logger.info(f"   ✅ Identificado como ESP32 MOTOR")
                                            return 'motor'
                                    
                                    # Verificar identificadores de garra
                                    for identifier in self.GARRA_IDENTIFIERS:
                                        if identifier.lower() in response_lower:
                                            logger.info(f"   ✅ Identificado como ESP32 GARRA")
                                            return 'garra'
                            
                            time.sleep(0.1)
                    
                    except Exception as e:
                        logger.debug(f"   ⚠️ Erro no comando {cmd}: {e}")
                        continue
                
                # Método 2: Verificar descrição da porta
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if p.device == port:
                        desc = p.description.lower()
                        
                        # Alguns ESP32 têm descrições específicas
                        if 'ch340' in desc or 'cp210' in desc or 'usb' in desc:
                            logger.info(f"   ℹ️ Porta USB genérica detectada: {desc}")
                
                logger.warning(f"   ❓ Não foi possível identificar ESP32 na porta {port}")
                return None
                
        except serial.SerialException as e:
            logger.debug(f"   ❌ Erro ao acessar porta {port}: {e}")
            return None
        except Exception as e:
            logger.debug(f"   ❌ Erro inesperado na porta {port}: {e}")
            return None
    
    def discover_by_test_commands(self, port: str) -> Optional[str]:
        """
        Identifica ESP32 enviando comandos de teste específicos
        Motor responde a comandos de movimento
        Garra responde a comandos de servo
        """
        try:
            with serial.Serial(port, self.baudrate, timeout=1.0) as ser:
                time.sleep(0.5)
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # Teste 1: Comando de movimento (deve funcionar no Motor)
                ser.write(b'{"comando":"status_motor"}\n')
                time.sleep(0.3)
                
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    if 'motor' in response.lower() or 'velocidade' in response.lower():
                        logger.info(f"   ✅ Responde a comandos de motor")
                        return 'motor'
                
                # Teste 2: Comando de servo (deve funcionar na Garra)
                ser.write(b'{"comando":"status_servo"}\n')
                time.sleep(0.3)
                
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    if 'servo' in response.lower() or 'garra' in response.lower():
                        logger.info(f"   ✅ Responde a comandos de servo")
                        return 'garra'
                
        except Exception as e:
            logger.debug(f"   ⚠️ Erro no teste de comandos: {e}")
        
        return None
    
    def discover_all(self) -> Dict[str, Optional[str]]:
        """
        Descobre automaticamente as portas dos dois ESP32
        
        Returns:
            {'motor': '/dev/ttyUSB0', 'garra': '/dev/ttyUSB1'}
        """
        logger.info("="*60)
        logger.info("🔍 INICIANDO DESCOBERTA AUTOMÁTICA DOS ESP32")
        logger.info("="*60)
        
        result = {
            'motor': None,
            'garra': None
        }
        
        # Listar todas as portas
        ports = self.list_available_ports()
        
        if not ports:
            logger.error("❌ Nenhuma porta serial encontrada!")
            return result
        
        # Filtrar apenas portas USB/ACM (ESP32)
        usb_ports = [
            p.device for p in ports 
            if 'USB' in p.device or 'ACM' in p.device
        ]
        
        if not usb_ports:
            logger.warning("⚠️ Nenhuma porta USB encontrada, tentando todas...")
            usb_ports = [p.device for p in ports]
        
        logger.info(f"\n📍 Portas a serem testadas: {usb_ports}")
        
        # Tentar identificar cada porta
        for port in usb_ports:
            # Método 1: Identificação por comando
            device_type = self.identify_esp32(port)
            
            # Método 2: Teste de comandos específicos
            if not device_type:
                device_type = self.discover_by_test_commands(port)
            
            if device_type:
                if device_type == 'motor' and not result['motor']:
                    result['motor'] = port
                    logger.info(f"✅ ESP32 MOTOR mapeado para: {port}")
                elif device_type == 'garra' and not result['garra']:
                    result['garra'] = port
                    logger.info(f"✅ ESP32 GARRA mapeado para: {port}")
        
        # Estratégia de fallback: se apenas um foi detectado
        if result['motor'] and not result['garra']:
            remaining = [p for p in usb_ports if p != result['motor']]
            if remaining:
                result['garra'] = remaining[0]
                logger.warning(f"⚠️ ESP32 GARRA não identificado, usando porta restante: {remaining[0]}")
        
        elif result['garra'] and not result['motor']:
            remaining = [p for p in usb_ports if p != result['garra']]
            if remaining:
                result['motor'] = remaining[0]
                logger.warning(f"⚠️ ESP32 MOTOR não identificado, usando porta restante: {remaining[0]}")
        
        # Se nenhum foi identificado mas há 2 portas
        elif not result['motor'] and not result['garra'] and len(usb_ports) >= 2:
            logger.warning("⚠️ Nenhum ESP32 identificado, usando ordem padrão:")
            result['motor'] = usb_ports[0]
            result['garra'] = usb_ports[1]
            logger.warning(f"   Motor: {usb_ports[0]} (tentativa)")
            logger.warning(f"   Garra: {usb_ports[1]} (tentativa)")
        
        # Resumo
        logger.info("\n" + "="*60)
        logger.info("📊 RESULTADO DA DESCOBERTA")
        logger.info("="*60)
        logger.info(f"🔧 ESP32 MOTOR: {result['motor'] or '❌ Não encontrado'}")
        logger.info(f"🤖 ESP32 GARRA: {result['garra'] or '❌ Não encontrado'}")
        logger.info("="*60)
        
        return result
    
    def save_to_config(self, config_file: str = 'esp32_ports.json'):
        """Salva as portas descobertas em arquivo de configuração"""
        result = self.discover_all()
        
        config = {
            'motor_port': result['motor'],
            'garra_port': result['garra'],
            'timestamp': time.time(),
            'auto_discovered': True
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"✅ Configuração salva em {config_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar configuração: {e}")
            return False


def load_discovered_ports(config_file: str = 'esp32_ports.json') -> Dict[str, Optional[str]]:
    """Carrega portas descobertas anteriormente"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        logger.info(f"📂 Configuração carregada de {config_file}")
        logger.info(f"   Motor: {config.get('motor_port')}")
        logger.info(f"   Garra: {config.get('garra_port')}")
        
        return {
            'motor': config.get('motor_port'),
            'garra': config.get('garra_port')
        }
    except FileNotFoundError:
        logger.info(f"ℹ️ Arquivo {config_file} não encontrado")
        return {'motor': None, 'garra': None}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {e}")
        return {'motor': None, 'garra': None}


# Teste standalone
if __name__ == "__main__":
    print("🧪 TESTE DE DESCOBERTA AUTOMÁTICA DOS ESP32")
    print("="*60)
    
    discovery = ESP32Discovery()
    
    # Opção 1: Descobrir e mostrar resultado
    result = discovery.discover_all()
    
    # Opção 2: Descobrir e salvar em arquivo
    print("\n💾 Salvando configuração...")
    discovery.save_to_config('esp32_ports.json')
    
    print("\n✅ Teste concluído!")
    print("\n💡 Para usar no código:")
    print("   from esp32_discovery import ESP32Discovery")
    print("   discovery = ESP32Discovery()")
    print("   ports = discovery.discover_all()")
    print("   motor_port = ports['motor']")
    print("   garra_port = ports['garra']")
