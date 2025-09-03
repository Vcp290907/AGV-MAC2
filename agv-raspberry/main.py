"""
Sistema principal do AGV Raspberry Pi
Coordena todos os módulos: controle, hardware, câmera e comunicação
"""

import asyncio
import logging
from comunicacao.api_local import iniciar_servidor
from controle.navegacao import ControladorNavegacao
from hardware.esp32_interface import ESP32Interface
from camera.vision_system import VisionSystem

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AGVSystem:
    def __init__(self):
        self.navegacao = ControladorNavegacao()
        self.esp32 = ESP32Interface()
        self.camera = VisionSystem()
        self.ativo = False
        
    async def inicializar(self):
        """Inicializa todos os subsistemas"""
        logger.info("🚀 Inicializando sistema AGV...")
        
        # Inicializar hardware
        await self.esp32.conectar()
        await self.camera.inicializar()
        
        # Configurar navegação
        self.navegacao.configurar(self.esp32, self.camera)
        
        self.ativo = True
        logger.info("✅ Sistema AGV pronto!")
        
    async def executar_comando(self, comando):
        """Executa comando recebido da interface web"""
        if not self.ativo:
            return {"erro": "Sistema não inicializado"}
            
        tipo = comando.get('tipo')
        
        if tipo == 'mover':
            return await self.navegacao.mover_para(comando['destino'])
        elif tipo == 'parar':
            return await self.navegacao.parar()
        elif tipo == 'status':
            return await self.obter_status()
        else:
            return {"erro": "Comando não reconhecido"}
            
    async def obter_status(self):
        """Retorna status completo do sistema"""
        return {
            "ativo": self.ativo,
            "posicao": await self.navegacao.obter_posicao(),
            "bateria": await self.esp32.obter_bateria(),
            "camera_ativa": self.camera.esta_ativa(),
            "timestamp": asyncio.get_event_loop().time()
        }

async def main():
    """Função principal"""
    agv = AGVSystem()
    
    try:
        # Inicializar sistema
        await agv.inicializar()
        
        # Iniciar servidor de comunicação
        await iniciar_servidor(agv)
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
    finally:
        logger.info("🔄 Finalizando sistema AGV...")

if __name__ == "__main__":
    asyncio.run(main())
