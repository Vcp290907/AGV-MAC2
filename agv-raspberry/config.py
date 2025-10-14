#!/usr/bin/env python3
"""
Configurações do Sistema AGV - Raspberry Pi
"""

import os
from typing import Dict, Any

# Configurações de rede
NETWORK_CONFIG = {
    'pc_ip': os.getenv('PC_IP', '192.168.0.120'),  # IP do PC principal
    'pc_port': int(os.getenv('PC_PORT', '5000')),  # Porta do PC
    'local_port': int(os.getenv('LOCAL_PORT', '8080')),  # Porta local do Raspberry
    'wifi_ssid': os.getenv('WIFI_SSID', 'AGV_NETWORK'),
    'wifi_password': os.getenv('WIFI_PASSWORD', 'agv_password'),
    'auto_discovery': True  # Descoberta automática do PC
}

# Configurações de hardware
HARDWARE_CONFIG = {
    'camera': {
        'enabled': True,
        'resolution': (720, 1024),  # 720p padrão, boa taxa de quadros
        'fps': 30,
        'qr_detection': True,
    'device': 1,  # usar câmera 1 (/dev/video1)
        # Fração vertical onde começa a ROI (0.0 topo, 1.0 base). Menor valor = mais área.
        'roi_y_start_frac': 0.15,
        # Controles opcionais de exposição/ganho; se auto=True, manual é ignorado.
        'exposure': {
            'auto': True,
            'awb_auto': True,
            # 'exposure_time': 8000,       # microssegundos (exemplo, usar quando auto=False)
            # 'analogue_gain': 2.0         # ganho analógico (exemplo, usar quando auto=False)
        }
    },
    'esp32': {
        'enabled': True,
        'port': '/dev/ttyACM0',  # Porta USB do ESP32 - ALTERE AQUI se necessário
        'baudrate': 115200,
        'timeout': 2
    },
    'motors': {
        'max_speed': 100,  # Velocidade máxima (%)
        'acceleration': 50,  # Aceleração (%)
        'deceleration': 50,   # Desaceleração (%)
        # Inverter comandos de giro (se a fiação/firmware estiver invertida)
        'invert_turn_commands': True
    },
    'sensors': {
        'ultrasonic': {
            'enabled': True,
            'trigger_pin': 23,
            'echo_pin': 24,
            'max_distance': 200  # cm
        },
        'imu': {
            'enabled': False,  # MPU6050
            'address': 0x68
        }
    }
}

# Configurações do sistema
SYSTEM_CONFIG = {
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_file': '/var/log/agv_raspberry.log',
    'data_directory': '/home/pi/agv_data',
    'backup_interval': 3600,  # Backup a cada hora
    'heartbeat_interval': 10,  # Heartbeat a cada 10 segundos
    'status_update_interval': 5,  # Atualização de status a cada 5 segundos
    'command_poll_interval': 2,  # Verificação de comandos a cada 2 segundos
    'data_sync_interval': 60  # Sincronização de dados a cada minuto
}

# Configurações de navegação
NAVIGATION_CONFIG = {
    'map_size': (1000, 1000),  # Tamanho do mapa em cm
    'grid_resolution': 10,  # Resolução da grade em cm
    'safety_margin': 20,  # Margem de segurança em cm
    'max_path_length': 500,  # Comprimento máximo do caminho em cm
    'path_planning_algorithm': 'astar',  # Algoritmo de planejamento de caminho
    'obstacle_detection_range': 50,  # Alcance de detecção de obstáculos em cm

    # Parâmetros do seguidor de linha e entrada no subcorredor (tuning rápido)
    'line_following': {
        'speed_base': 50,
        'speed_min': 20,
        'speed_max': 70,
        'steering_gain': 1.6
    },
    'subcorredor_entry': {
        'forward_seconds': 4.0,     # tempo de avanço antes da curva
        'forward_speed': None,       # se None, usa speed_base do seguidor de linha
        'turn_direction': 'direita', # 'direita' ou 'esquerda'
        'turn_angle_deg': 90         # ângulo da curva
    },
    'qr_centering': {
        'enabled': False,
        'timeout_s': 4.0,
        'tolerance_px': 24,       # quanto o centro pode diferir do centro da imagem
        'rotate_speed': 12,       # velocidade do pulso de rotação
        'rotate_pulse_s': 0.08,   # duração do pulso de rotação
        'forward_speed': None,    # se None, usa speed_base
        'forward_pulse_s': 0.10   # pequeno avanço para manter QR visível
    },
    'turn': {
    'strategy': 'vision_center',   # 'vision_center' | 'gyro' | 'time'
        # Inverter comandos de curva globalmente (alternativo ao hardware.motors)
        'invert_commands': True,
        'simple_mode': True,          # modo simples: rápido até faltar X graus, depois desacelera
        'slowdown_start_deg': 10.0,   # começa a desacelerar faltando X graus (modo simples)
        'simple_rate_brake_thresh': 25.0, # se a taxa for maior que isso ao entrar na zona lenta, dá um breve freio
        'simple_brake_pause_s': 0.09, # pausa após o freio rápido na transição para zona lenta
        'simple_pulse_s': 0.05,       # duração dos pulsos no modo simples na zona lenta
        'simple_pause_s': 0.05,       # pausa entre pulsos no modo simples na zona lenta
        'simple_disable_sign_flip': True, # desabilita freio por cruzamento no modo simples
        'max_speed': 22,                # velocidade máxima de giro (reduzido para menos overshoot)
        'min_speed': 6,                 # velocidade mínima de giro
        'slowdown_threshold_deg': 30.0, # começa a desacelerar ao se aproximar (graus)
        'stop_tolerance_deg': 0.8,      # tolerância para parar no alvo (graus)
        'inertia_comp_deg': 2.0,        # compensação base de inércia (graus)
        'inertia_rate_k': 0.03,         # ganho adicional pela taxa angular (graus/seg)
        'speed_k': 1.0,                 # ganho para curva de velocidade
        'slowdown_gamma': 1.8,          # mapeamento exponencial da desaceleração (>=1)
        'brake_pause_s': 0.45,          # pausa para estabilizar após parar
        'sign_flip_brake': True,        # frear imediatamente ao cruzar o ponto de parada
        'dynamic_compensation': True,   # atualizar compensação de inércia dinamicamente
        'creep_threshold_deg': 3.0,     # abaixo deste erro, entrar em modo de pulsos curtos
        'creep_pulse_s': 0.06,          # duração do pulso no modo creep
        'creep_pause_s': 0.05,          # pausa entre pulsos de creep
        'max_rate_deg_s': 180.0,        # filtro anti-glitch: taxa máxima plausível
        'max_jump_deg': 45.0,           # filtro anti-glitch: salto máximo plausível entre leituras
        # Parâmetros do modo visão (parar quando a linha centraliza)
        'vision': {
            'exclusive': True,     # usar somente câmera para a curva (sem giroscópio)
            'tolerance_px': 22,     # quão perto do alvo parar (px)
            'slowdown_px': 110,     # abaixo disso, usa velocidade lenta (px)
            'target_offset_px': 18, # para parar um pouco antes do centro: direita usa -offset, esquerda +offset
            'min_confidence': 0.45, # confiança mínima da linha
            'timeout_s': 8.0,       # tempo máximo procurando a linha durante a curva
            'speed_fast': 22,       # velocidade rápida
            'speed_slow': 8,        # velocidade lenta na aproximação
            'start_delay_s': 0.0,   # sem pré-giro quando exclusivo
            'start_progress_deg': 0.0 # sem pré-giro quando exclusivo
        },
        # Parâmetros do modo tempo (curva baseada em duração)
        'time': {
            'seconds_right': 1.2,
            'seconds_left': 1.2,
            'speed': 20
        }
    }
}

# Configurações de visão computacional
VISION_CONFIG = {
    'qr_code': {
        'enabled': True,
        'detection_area': (0.2, 0.8, 0.2, 0.8),  # Área de detecção (x1, x2, y1, y2)
        'min_size': 50,  # Tamanho mínimo do QR code em pixels
        'max_size': 300,  # Tamanho máximo do QR code em pixels
        'confidence_threshold': 0.7  # Limite de confiança para detecção
    },
    'obstacle_detection': {
        'enabled': True,
        'min_area': 1000,  # Área mínima para considerar obstáculo
        'max_distance': 200  # Distância máxima para detecção
    },
    'color_tracking': {
        'enabled': False,
        'target_color': [0, 255, 0],  # Verde (BGR)
        'color_tolerance': 30
    }
}

# Configurações de controle de motores
MOTOR_CONFIG = {
    'pid': {
        'kp': 1.0,  # Ganho proporcional
        'ki': 0.1,  # Ganho integral
        'kd': 0.05  # Ganho derivativo
    },
    'wheel_diameter': 6.5,  # Diâmetro da roda em cm
    'wheel_base': 20.0,  # Distância entre rodas em cm
    'encoder_pulses_per_revolution': 20,  # Pulsos do encoder por revolução
    'max_linear_speed': 50,  # Velocidade linear máxima em cm/s
    'max_angular_speed': 180  # Velocidade angular máxima em graus/s
}

# Configurações de bateria e energia
BATTERY_CONFIG = {
    'monitoring': {
        'enabled': True,
        'voltage_pin': 26,
        'current_pin': 27,
        'reference_voltage': 3.3,
        'adc_resolution': 1024,
        'battery_capacity': 2000,  # Capacidade em mAh
        'low_battery_threshold': 20,  # % para alerta de bateria baixa
        'critical_battery_threshold': 10  # % para parada de emergência
    }
}

def get_config() -> Dict[str, Any]:
    """Retorna todas as configurações"""
    return {
        'network': NETWORK_CONFIG,
        'hardware': HARDWARE_CONFIG,
        'system': SYSTEM_CONFIG,
        'navigation': NAVIGATION_CONFIG,
        'vision': VISION_CONFIG,
        'motor': MOTOR_CONFIG,
        'battery': BATTERY_CONFIG
    }

def get_config_value(section: str, key: str, default=None):
    """Obtém um valor específico de configuração"""
    config = get_config()

    if section in config and key in config[section]:
        return config[section][key]

    return default

def update_config(section: str, key: str, value: Any):
    """Atualiza um valor de configuração"""
    if section == 'network':
        NETWORK_CONFIG[key] = value
    elif section == 'hardware':
        HARDWARE_CONFIG[key] = value
    elif section == 'system':
        SYSTEM_CONFIG[key] = value
    elif section == 'navigation':
        NAVIGATION_CONFIG[key] = value
    elif section == 'vision':
        VISION_CONFIG[key] = value
    elif section == 'motor':
        MOTOR_CONFIG[key] = value
    elif section == 'battery':
        BATTERY_CONFIG[key] = value

# Funções específicas para ESP32
def get_esp32_config() -> Dict[str, Any]:
    """Retorna configuração completa do ESP32"""
    return HARDWARE_CONFIG['esp32'].copy()

def get_esp32_port() -> str:
    """Retorna apenas a porta do ESP32"""
    return HARDWARE_CONFIG['esp32'].get('port', '/dev/ttyACM0')

def get_esp32_baudrate() -> int:
    """Retorna baudrate do ESP32"""
    return HARDWARE_CONFIG['esp32'].get('baudrate', 115200)

def get_esp32_timeout() -> float:
    """Retorna timeout do ESP32"""
    return HARDWARE_CONFIG['esp32'].get('timeout', 1)

def auto_detect_esp32_port() -> str:
    """Detecta automaticamente a porta do ESP32 e atualiza o config"""
    import serial.tools.list_ports
    import serial
    
    ports = serial.tools.list_ports.comports()
    usb_ports = [p.device for p in ports if 'USB' in p.device or 'ACM' in p.device]
    
    for port in usb_ports:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            ser.write(b'{"comando": "ping"}\n')
            response = ser.readline().decode().strip()
            ser.close()
            
            if response and '"status": "ok"' in response:
                # Atualizar config
                HARDWARE_CONFIG['esp32']['port'] = port
                print(f"✅ Porta ESP32 detectada e atualizada: {port}")
                return port
        except:
            pass
    
    print("❌ ESP32 não encontrado automaticamente")
    return HARDWARE_CONFIG['esp32']['port']

if __name__ == "__main__":
    # Script para testar e atualizar configuração
    print("🔧 Teste de Configuração AGV")
    print("=" * 40)
    
    print(f"📡 Porta ESP32 atual: {get_esp32_port()}")
    
    # Tentar detectar automaticamente
    detected_port = auto_detect_esp32_port()
    if detected_port != get_esp32_port():
        print(f"✅ Porta atualizada para: {detected_port}")
    else:
        print("ℹ️  Porta já está correta")
    
    print(f"🔧 Configuração final: {get_esp32_config()}")

def save_config_to_file(filepath: str = '/home/pi/agv_config.json'):
    """Salva configurações em arquivo"""
    try:
        config = get_config()
        with open(filepath, 'w') as f:
            import json
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        return False

def load_config_from_file(filepath: str = '/home/pi/agv_config.json'):
    """Carrega configurações de arquivo"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                import json
                config = json.load(f)

            # Atualizar configurações globais
            global NETWORK_CONFIG, HARDWARE_CONFIG, SYSTEM_CONFIG
            global NAVIGATION_CONFIG, VISION_CONFIG, MOTOR_CONFIG, BATTERY_CONFIG

            NETWORK_CONFIG.update(config.get('network', {}))
            HARDWARE_CONFIG.update(config.get('hardware', {}))
            SYSTEM_CONFIG.update(config.get('system', {}))
            NAVIGATION_CONFIG.update(config.get('navigation', {}))
            VISION_CONFIG.update(config.get('vision', {}))
            MOTOR_CONFIG.update(config.get('motor', {}))
            BATTERY_CONFIG.update(config.get('battery', {}))

            return True
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")

    return False

# Carregar configurações do arquivo na inicialização
load_config_from_file()