"""
Sistema de Navegação do AGV
Controla movimento, trajetórias e lógica de navegação
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

class ControladorNavegacao:
    def __init__(self):
        self.posicao_atual = {"x": 0, "y": 0, "orientacao": 0}
        self.esp32 = None
        self.camera = None
        self.em_movimento = False
        
    def configurar(self, esp32_interface, vision_system):
        """Configura as dependências do sistema de navegação"""
        self.esp32 = esp32_interface
        self.camera = vision_system
        logger.info("🧭 Sistema de navegação configurado")
        
    async def mover_para(self, destino):
        """Move o AGV para o destino especificado"""
        logger.info(f"🚚 Movendo para: {destino}")
        
        try:
            self.em_movimento = True
            
            # Calcular trajetória
            trajetoria = await self._calcular_trajetoria(destino)
            
            # Executar movimento
            for ponto in trajetoria:
                await self._mover_para_ponto(ponto)
                
                # Verificar obstáculos
                if await self._detectar_obstaculo():
                    logger.warning("⚠️ Obstáculo detectado, parando...")
                    await self.parar()
                    return {"status": "parado", "motivo": "obstáculo"}
                    
            self.em_movimento = False
            logger.info(f"✅ Chegou ao destino: {destino}")
            
            return {
                "status": "concluído",
                "destino": destino,
                "posicao_final": self.posicao_atual
            }
            
        except Exception as e:
            self.em_movimento = False
            logger.error(f"❌ Erro na navegação: {e}")
            return {"status": "erro", "detalhes": str(e)}
            
    async def parar(self):
        """Para o movimento do AGV"""
        logger.info("🛑 Parando AGV...")
        
        if self.esp32:
            await self.esp32.enviar_comando("PARAR")
            
        self.em_movimento = False
        return {"status": "parado", "posicao": self.posicao_atual}
        
    async def obter_posicao(self):
        """Retorna a posição atual do AGV"""
        return self.posicao_atual
        
    async def _calcular_trajetoria(self, destino):
        """Calcula a trajetória otimizada para o destino"""
        # Simulação simples - na prática usaria algoritmos como A*
        return [
            {"x": 1, "y": 1},
            {"x": 2, "y": 2},
            {"x": 3, "y": 3}  # Pontos da trajetória
        ]
        
    async def _mover_para_ponto(self, ponto):
        """Move o AGV para um ponto específico"""
        logger.info(f"🎯 Movendo para ponto: {ponto}")
        
        # Enviar comando para ESP32
        if self.esp32:
            comando = f"MOVER:{ponto['x']},{ponto['y']}"
            await self.esp32.enviar_comando(comando)
            
        # Simular tempo de movimento
        await asyncio.sleep(1)
        
        # Atualizar posição atual
        self.posicao_atual = ponto
        
    async def _detectar_obstaculo(self):
        """Detecta obstáculos usando a câmera"""
        if not self.camera:
            return False
            
        # Usar sistema de visão para detectar obstáculos
        return await self.camera.detectar_obstaculo()
