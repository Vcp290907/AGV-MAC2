"""
Interface com ESP32
Gerencia comunicação serial e controle de hardware
"""

import serial
import asyncio
import logging

logger = logging.getLogger(__name__)

class ESP32Interface:
    def __init__(self, porta="/dev/ttyUSB0", baudrate=115200):
        self.porta = porta
        self.baudrate = baudrate
        self.serial_conn = None
        self.conectado = False
        
    async def conectar(self):
        """Estabelece conexão serial com ESP32"""
        try:
            logger.info(f"🔌 Conectando ao ESP32 na porta {self.porta}...")
            
            self.serial_conn = serial.Serial(
                port=self.porta,
                baudrate=self.baudrate,
                timeout=1
            )
            
            # Teste de comunicação
            await self.enviar_comando("PING")
            resposta = await self.ler_resposta()
            
            if "PONG" in resposta:
                self.conectado = True
                logger.info("✅ ESP32 conectado com sucesso!")
            else:
                logger.warning("⚠️ ESP32 não respondeu corretamente")
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ESP32: {e}")
            self.conectado = False
            
    async def enviar_comando(self, comando):
        """Envia comando para o ESP32"""
        if not self.conectado or not self.serial_conn:
            logger.warning("⚠️ ESP32 não conectado")
            return False
            
        try:
            logger.debug(f"📤 Enviando: {comando}")
            self.serial_conn.write(f"{comando}\n".encode())
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar comando: {e}")
            return False
            
    async def ler_resposta(self, timeout=5):
        """Lê resposta do ESP32"""
        if not self.conectado or not self.serial_conn:
            return ""
            
        try:
            # Aguardar resposta com timeout
            inicio = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - inicio) < timeout:
                if self.serial_conn.in_waiting > 0:
                    resposta = self.serial_conn.readline().decode().strip()
                    logger.debug(f"📥 Recebido: {resposta}")
                    return resposta
                await asyncio.sleep(0.1)
                
            logger.warning("⏰ Timeout ao aguardar resposta do ESP32")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Erro ao ler resposta: {e}")
            return ""
            
    async def obter_bateria(self):
        """Obtém nível da bateria do ESP32"""
        if await self.enviar_comando("BATERIA"):
            resposta = await self.ler_resposta()
            try:
                # Espera resposta no formato "BATERIA:85"
                if "BATERIA:" in resposta:
                    return int(resposta.split(":")[1])
            except:
                pass
        return 0
        
    async def mover_motores(self, esquerda, direita):
        """Controla velocidade dos motores"""
        comando = f"MOTOR:{esquerda},{direita}"
        return await self.enviar_comando(comando)
        
    async def parar_motores(self):
        """Para todos os motores"""
        return await self.enviar_comando("PARAR")
        
    def desconectar(self):
        """Fecha conexão com ESP32"""
        if self.serial_conn:
            self.serial_conn.close()
            self.conectado = False
            logger.info("🔌 ESP32 desconectado")
