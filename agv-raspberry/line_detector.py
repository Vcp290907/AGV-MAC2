#!/usr/bin/env python3
"""
Detector de Linha Preta para AGV - Versão Picamera2
Sistema de visão computacional para detectar e seguir linha preta no chão
"""

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("Picamera2 nao disponivel - usando simulacao")

import cv2
import numpy as np
import time
import sys

class LineDetector:
    """Detector de linha preta usando Picamera2"""

    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.picam2 = None

        # Configurações de processamento de imagem - MAIS TOLERANTE
        self.lower_black = np.array([0, 0, 0])
        self.upper_black = np.array([180, 255, 120])  # Mais tolerante

        # Configurações de detecção de linha
        self.min_line_width = 5   # Menor largura mínima
        self.max_line_width = 400 # Maior largura máxima (para interseções em T)
        self.line_center_offset = 0  # Offset do centro da linha

        # ROI (Region of Interest) - área inferior da imagem
        self.roi_y_start = int(height * 0.4)  # 40% inferior (mais área)
        self.roi_height = height - self.roi_y_start

        # PID para controle de direção
        self.kp = 0.5
        self.ki = 0.0
        self.kd = 0.1
        self.previous_error = 0
        self.integral = 0

        # Estado da linha
        self.line_detected = False
        self.line_center = width // 2
        self.line_width = 0
        self.line_confidence = 0

    def initialize(self):
        """Inicializar Picamera2 para detecção de linha"""
        print("Inicializando Picamera2 para detecção de linha...")

        if PICAMERA2_AVAILABLE:
            try:
                self.picam2 = Picamera2(camera_num=1)  # Câmera inferior
                config = self.picam2.create_preview_configuration(
                    main={"format": 'XRGB8888', "size": (self.width, self.height)}
                )
                self.picam2.configure(config)
                self.picam2.start()

                # Testar captura
                frame = self.picam2.capture_array()
                if frame is not None:
                    print("✅ Picamera2 inicializada para detecção de linha!")
                    return True
                else:
                    print("❌ Falha ao capturar frame de teste")
                    return False

            except Exception as e:
                print(f"❌ Erro ao inicializar Picamera2: {e}")
                return False
        else:
            print("⚠️ Picamera2 não disponível - modo simulação ativado")
            print("✅ Detector de linha inicializado (simulação)")
            return True

    def preprocess_image(self, frame):
        """Pré-processar imagem para detecção de linha"""
        try:
            # Converter de XRGB para BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Recortar ROI (apenas área inferior)
            roi = frame[self.roi_y_start:self.roi_y_start + self.roi_height, :]

            # Converter para HSV
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # Aplicar filtro de cor para detectar preto
            mask = cv2.inRange(hsv, self.lower_black, self.upper_black)

            # Aplicar operações morfológicas para limpar ruído
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            return mask, roi

        except Exception as e:
            print(f"Erro no pré-processamento: {e}")
            return None, None

    def detect_line(self, mask):
        """Detectar linha preta na máscara"""
        try:
            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                print(f"Debug: Nenhum contorno encontrado")
                self.line_detected = False
                return False

            # DEBUG: Mostrar número de contornos
            print(f"Debug: {len(contours)} contornos encontrados")

            # Encontrar maior contorno (provavelmente a linha)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            print(f"Debug: Maior contorno area = {area}")

            # Calcular bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)
            print(f"Debug: Bounding box = ({x}, {y}, {w}, {h})")

            # Verificar se é uma linha válida - MAIS TOLERANTE
            if w < self.min_line_width:
                print(f"Debug: Linha muito fina (w={w} < {self.min_line_width})")
                self.line_detected = False
                return False

            if w > self.max_line_width:
                print(f"Debug: Linha muito larga (w={w} > {self.max_line_width})")
                self.line_detected = False
                return False

            # Calcular centro da linha
            line_center = x + w // 2
            line_width = w

            # Calcular confiança baseada na área e proporção
            expected_area = w * h
            confidence = min(area / expected_area, 1.0) if expected_area > 0 else 0

            print(f"Debug: Linha detectada - Centro: {line_center}, Largura: {line_width}, Confiança: {confidence:.2f}")

            # Atualizar estado
            self.line_detected = True
            self.line_center = line_center
            self.line_width = line_width
            self.line_confidence = confidence

            return True

        except Exception as e:
            print(f"Erro na detecção de linha: {e}")
            self.line_detected = False
            return False

    def calculate_steering_correction(self):
        """Calcular correção de direção usando PID"""
        if not self.line_detected:
            return 0

        # Centro da imagem
        image_center = self.width // 2

        # Erro: diferença entre centro da linha e centro da imagem
        error = self.line_center - image_center + self.line_center_offset

        # PID
        self.integral += error
        derivative = error - self.previous_error
        correction = self.kp * error + self.ki * self.integral + self.kd * derivative

        self.previous_error = error

        # Limitar correção entre -1 e 1
        correction = max(-1.0, min(1.0, correction))

        return correction

    def get_line_info(self):
        """Retornar informações sobre a linha detectada"""
        return {
            'detected': self.line_detected,
            'center': self.line_center,
            'width': self.line_width,
            'confidence': self.line_confidence,
            'steering_correction': self.calculate_steering_correction(),
            'timestamp': time.time()
        }

    def process_frame(self, frame=None):
        """Processar um frame completo"""
        try:
            if frame is None and self.picam2:
                frame = self.picam2.capture_array()

            if frame is None:
                return None

            # Pré-processar
            mask, roi = self.preprocess_image(frame)
            if mask is None:
                return None

            # DEBUG: Contar pixels pretos
            black_pixels = cv2.countNonZero(mask)
            total_pixels = mask.size
            black_ratio = black_pixels / total_pixels
            print(f"Debug: Pixels pretos: {black_pixels}/{total_pixels} ({black_ratio:.2%})")

            # Detectar linha
            line_found = self.detect_line(mask)

            # Retornar informações
            info = self.get_line_info()
            info['mask'] = mask
            info['roi'] = roi
            info['debug_black_ratio'] = black_ratio

            return info

        except Exception as e:
            print(f"Erro no processamento do frame: {e}")
            return None

    def visualize_detection(self, frame, info):
        """Visualizar detecção da linha no frame"""
        try:
            if info and info['detected']:
                # Desenhar ROI
                cv2.rectangle(frame, (0, self.roi_y_start),
                            (self.width, self.roi_y_start + self.roi_height),
                            (255, 0, 0), 2)

                # Desenhar centro da linha
                center_x = info['center']
                center_y = self.roi_y_start + self.roi_height // 2
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)

                # Desenhar linha central da imagem
                cv2.line(frame, (self.width // 2, self.roi_y_start),
                        (self.width // 2, self.roi_y_start + self.roi_height),
                        (255, 255, 0), 1)

                # Mostrar informações
                text_lines = [
                    f"Linha: {'Detectada' if info['detected'] else 'Nao detectada'}",
                    f"Centro: {info['center']}",
                    f"Largura: {info['width']}",
                    f"Conf: {info['confidence']:.2f}",
                    f"Correcao: {info['steering_correction']:.2f}"
                ]

                for i, text in enumerate(text_lines):
                    cv2.putText(frame, text, (10, 30 + i * 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            return frame

        except Exception as e:
            print(f"Erro na visualizacao: {e}")
            return frame

    def cleanup(self):
        """Limpar recursos"""
        if self.picam2:
            self.picam2.stop()
            print("🛑 Picamera2 liberada")

def main():
    """Função principal para teste"""
    print("🎯 TESTE DO DETECTOR DE LINHA PRETA - PICAMERA2")
    print("=" * 50)

    # Criar detector
    detector = LineDetector()

    # Inicializar
    if not detector.initialize():
        return

    try:
        print("Pressione 'q' para sair, 'r' para resetar PID")
        print("A câmera CSI deve estar apontada para o chão")

        while True:
            # Processar frame
            info = detector.process_frame()

            if info:
                # Criar frame para visualização
                vis_frame = np.zeros((detector.height, detector.width, 3), dtype=np.uint8)

                # Adicionar ROI e máscara
                if 'roi' in info and 'mask' in info:
                    # Converter máscara para BGR
                    mask_bgr = cv2.cvtColor(info['mask'], cv2.COLOR_GRAY2BGR)

                    # Combinar ROI original com máscara
                    combined = cv2.addWeighted(info['roi'], 0.7, mask_bgr, 0.3, 0)

                    # Colocar na visualização
                    vis_frame[detector.roi_y_start:detector.roi_y_start + detector.roi_height, :] = combined

                # Visualizar detecção
                vis_frame = detector.visualize_detection(vis_frame, info)

                # Mostrar frame
                cv2.imshow("Detector de Linha Preta - Picamera2", vis_frame)

            # Verificar teclas
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('r'):
                detector.previous_error = 0
                detector.integral = 0
                print("🔄 PID resetado")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")

    finally:
        detector.cleanup()
        cv2.destroyAllWindows()

        # Resumo final
        print("\n📊 RESUMO FINAL:")
        print("   Sistema de detecção de linha testado com Picamera2")

if __name__ == "__main__":
    main()
