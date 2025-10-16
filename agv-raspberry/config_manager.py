#!/usr/bin/env python3
"""
Gerenciador de Configurações do AGV - Arquivo JSON Simples
Carrega configurações de config.json e fornece acesso fácil
"""

import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """Gerenciador de configurações baseado em arquivo JSON"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self) -> bool:
        """Carrega configurações do arquivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ Configurações carregadas de {self.config_file}")
                return True
            else:
                print(f"⚠️ Arquivo de configuração não encontrado: {self.config_file}")
                print("ℹ️ Usando configurações padrão")
                self._create_default_config()
                return False
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            self._create_default_config()
            return False

    def save_config(self) -> bool:
        """Salva configurações no arquivo JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configurações salvas em {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
            return False

    def _create_default_config(self):
        """Cria configurações padrão"""
        self.config = {
            "backend": {
                "ip": "192.168.0.120",
                "port": 5000,
                "timeout": 5
            },
            "agv": {
                "id": "agv_1",
                "name": "AGV-001",
                "version": "1.0.0"
            },
            "camera": {
                "primary": "picamera2",
                "fallback": "opencv",
                "resolution": [640, 480],
                "fps": 30
            },
            "esp32": {
                "port": "/dev/ttyACM0",
                "baudrate": 115200,
                "timeout": 2
            },
            "navigation": {
                "line_following_speed": 50,
                "qr_detection_enabled": True,
                "obstacle_detection_enabled": False
            }
        }

    def get(self, key_path: str, default=None) -> Any:
        """Obtém valor usando caminho separado por pontos (ex: 'backend.ip')"""
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> bool:
        """Define valor usando caminho separado por pontos"""
        keys = key_path.split('.')
        config = self.config

        try:
            # Navegar até o penúltimo nível
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]

            # Definir o valor final
            config[keys[-1]] = value
            return True
        except Exception as e:
            print(f"❌ Erro ao definir configuração {key_path}: {e}")
            return False

    def get_backend_url(self, endpoint: str = "") -> str:
        """Retorna URL completa do backend"""
        ip = self.get('backend.ip', '192.168.0.120')
        port = self.get('backend.port', 5000)
        base_url = f"http://{ip}:{port}"
        return f"{base_url}/{endpoint}".rstrip('/')

    def get_esp32_config(self) -> Dict[str, Any]:
        """Retorna configuração do ESP32"""
        return {
            'port': self.get('esp32.port', '/dev/ttyACM0'),
            'baudrate': self.get('esp32.baudrate', 115200),
            'timeout': self.get('esp32.timeout', 2)
        }

    def get_camera_config(self) -> Dict[str, Any]:
        """Retorna configuração da câmera"""
        return {
            'primary': self.get('camera.primary', 'picamera2'),
            'fallback': self.get('camera.fallback', 'opencv'),
            'resolution': self.get('camera.resolution', [640, 480]),
            'fps': self.get('camera.fps', 30)
        }

    def get_agv_info(self) -> Dict[str, Any]:
        """Retorna informações do AGV"""
        return {
            'id': self.get('agv.id', 'agv_1'),
            'name': self.get('agv.name', 'AGV-001'),
            'version': self.get('agv.version', '1.0.0')
        }

    def print_config(self):
        """Imprime todas as configurações"""
        print("🔧 CONFIGURAÇÕES ATUAIS:")
        print("=" * 50)
        print(json.dumps(self.config, indent=2, ensure_ascii=False))

# Instância global do gerenciador
config_manager = ConfigManager()

# Funções de conveniência para uso direto
def get_config(key_path: str, default=None) -> Any:
    """Função de conveniência para obter configuração"""
    return config_manager.get(key_path, default)

def set_config(key_path: str, value: Any) -> bool:
    """Função de conveniência para definir configuração"""
    return config_manager.set(key_path, value)

def save_config() -> bool:
    """Função de conveniência para salvar configurações"""
    return config_manager.save_config()

def get_backend_url(endpoint: str = "") -> str:
    """Função de conveniência para obter URL do backend"""
    return config_manager.get_backend_url(endpoint)

if __name__ == "__main__":
    # Teste do gerenciador
    print("🧪 TESTE DO GERENCIADOR DE CONFIGURAÇÕES")
    print("=" * 50)

    # Carregar configurações
    config_manager.load_config()

    # Mostrar configurações atuais
    config_manager.print_config()

    # Testar getters
    print(f"\n📡 Backend IP: {get_config('backend.ip')}")
    print(f"📡 Backend URL: {get_backend_url()}")
    print(f"🤖 AGV ID: {get_config('agv.id')}")
    print(f"📷 Câmera primária: {get_config('camera.primary')}")

    # Testar setters
    print("\n🔧 Testando modificações...")
    set_config('backend.timeout', 10)
    set_config('navigation.line_following_speed', 60)

    print(f"⏱️ Novo timeout: {get_config('backend.timeout')}")
    print(f"🏎️ Nova velocidade: {get_config('navigation.line_following_speed')}")

    # Salvar
    save_config()