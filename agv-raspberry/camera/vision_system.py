"""
Sistema de Visão Computacional
Gerencia câmera e processamento de imagens para navegação
"""

import cv2
import numpy as np
import asyncio
import logging

logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.camera = None
        self.ativa = False
        self.frame_atual = None
        
    async def inicializar(self):
        """Inicializa o sistema de câmera"""
        try:
            logger.info("📷 Inicializando sistema de visão...")
            
            self.camera = cv2.VideoCapture(self.camera_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            if self.camera.isOpened():
                self.ativa = True
                logger.info("✅ Câmera inicializada com sucesso!")
                
                # Iniciar loop de captura
                asyncio.create_task(self._loop_captura())
            else:
                logger.error("❌ Falha ao abrir câmera")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar câmera: {e}")
            
    async def _loop_captura(self):
        """Loop contínuo de captura de frames"""
        while self.ativa:
            try:
                ret, frame = self.camera.read()
                if ret:
                    self.frame_atual = frame
                else:
                    logger.warning("⚠️ Falha na captura do frame")
                    
                await asyncio.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"❌ Erro na captura: {e}")
                await asyncio.sleep(1)
                
    async def detectar_obstaculo(self):
        """Detecta obstáculos no caminho usando visão computacional"""
        if not self.ativa or self.frame_atual is None:
            return False
            
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(self.frame_atual, cv2.COLOR_BGR2GRAY)
            
            # Aplicar blur para reduzir ruído
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Detecção de bordas
            edges = cv2.Canny(blurred, 50, 150)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Verificar se há contornos grandes (possíveis obstáculos)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Ajustar conforme necessário
                    logger.debug("🚧 Possível obstáculo detectado")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de obstáculos: {e}")
            return False
            
    async def detectar_linha(self):
        """Detecta linha no chão para seguimento"""
        if not self.ativa or self.frame_atual is None:
            return None
            
        try:
            # Região de interesse (parte inferior da imagem)
            height, width = self.frame_atual.shape[:2]
            roi = self.frame_atual[int(height*0.7):, :]
            
            # Converter para HSV para melhor detecção de cor
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Definir range para linha preta
            lower_black = np.array([0, 0, 0])
            upper_black = np.array([180, 255, 50])
            
            # Criar máscara
            mask = cv2.inRange(hsv, lower_black, upper_black)
            
            # Encontrar contornos da linha
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Pegar o maior contorno (linha principal)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Calcular centro da linha
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Retornar posição relativa ao centro da imagem
                    center_offset = cx - width // 2
                    return {"offset": center_offset, "confidence": 0.8}
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de linha: {e}")
            return None
            
    def obter_frame_atual(self):
        """Retorna o frame atual da câmera"""
        return self.frame_atual
        
    def esta_ativa(self):
        """Verifica se o sistema de visão está ativo"""
        return self.ativa
        
    def finalizar(self):
        """Finaliza o sistema de visão"""
        self.ativa = False
        if self.camera:
            self.camera.release()
        logger.info("📷 Sistema de visão finalizado")
