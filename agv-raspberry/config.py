#!/usr/bin/env python3
"""
Configurações do Sistema AGV - Raspberry Pi
"""

import os
from typing import Dict, Any

# Configurações de rede
NETWORK_CONFIG = {
    'pc_ip': os.getenv('PC_IP', '192.168.0.100'),  # IP do PC principal
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
        'resolution': (640, 480),
        'fps': 30,
        'qr_detection': True,
        'device': 0  # /dev/video0
    },
    'esp32': {
        'enabled': True,
        'port': '/dev/ttyUSB0',  # Porta USB do ESP32
        'baudrate': 115200,
        'timeout': 1
    },
    'motors': {
        'max_speed': 100,  # Velocidade máxima (%)
        'acceleration': 50,  # Aceleração (%)
        'deceleration': 50   # Desaceleração (%)
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
    'obstacle_detection_range': 50  # Alcance de detecção de obstáculos em cm
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