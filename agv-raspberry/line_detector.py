#!/usr/bin/env python3
"""
Detector de Linha Preta para AGV
Sistema de visão computacional para detectar e seguir linha preta no chão
"""

import cv2
import numpy as np
import time
import sys

class LineDetector:
    """Detector de linha preta usando câmera inferior"""

    def __init__(self, camera_id=1, width=640, height=480):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None

        # Configurações de processamento de imagem
        self.lower_black = np.array([0, 0, 0])
        self.upper_black = np.array([180, 255, 50])

        # Configurações de detecção de linha
        self.min_line_width = 10
        self.max_line_width = 100
        self.line_center_offset = 0  # Offset do centro da linha

        # ROI (Region of Interest) - área inferior da imagem
        self.roi_y_start = int(height * 0.6)  # 60% inferior da imagem
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
        """Inicializar câmera para detecção de linha"""
        print(f"Inicializando câmera para detecção de linha (ID: {self.camera_id})...")

        # Tentar diferentes backends
        backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]

        for backend in backends:
            try:
                print(f"Tentando backend: {backend}")
                self.cap = cv2.VideoCapture(self.camera_id, backend)

                if self.cap.isOpened():
                    print(f"Backend {backend} funcionou!")
                    break
                else:
                    self.cap.release()
            except Exception as e:
                print(f"Erro com backend {backend}: {e}")
                continue

        if not self.cap or not self.cap.isOpened():
            print(f"❌ Não foi possível abrir câmera {self.camera_id}")
            return False

        # Configurar resolução
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Testar captura
        ret, frame = self.cap.read()
        if ret and frame is not None:
            print("✅ Câmera para detecção de linha inicializada!")
            return True
        else:
            print("❌ Falha ao capturar frame de teste")
            self.cap.release()
            return False

    def preprocess_image(self, frame):
        """Pré-processar imagem para detecção de linha"""
        try:
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
                self.line_detected = False
                return False

            # Encontrar maior contorno (provavelmente a linha)
            largest_contour = max(contours, key=cv2.contourArea)

            # Calcular bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Verificar se é uma linha válida
            if w < self.min_line_width or w > self.max_line_width:
                self.line_detected = False
                return False

            # Calcular centro da linha
            line_center = x + w // 2
            line_width = w

            # Calcular confiança baseada na área e proporção
            area = cv2.contourArea(largest_contour)
            expected_area = w * h
            confidence = min(area / expected_area, 1.0) if expected_area > 0 else 0

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
            if frame is None:
                if not self.cap or not self.cap.isOpened():
                    return None

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    return None

            # Pré-processar
            mask, roi = self.preprocess_image(frame)
            if mask is None:
                return None

            # Detectar linha
            line_found = self.detect_line(mask)

            # Retornar informações
            info = self.get_line_info()
            info['mask'] = mask
            info['roi'] = roi

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
                    f"Linha: {'Detectada' if info['detected'] else 'Não detectada'}",
                    f"Centro: {info['center']}",
                    f"Largura: {info['width']}",
                    ".2f",
                    ".2f"
                ]

                for i, text in enumerate(text_lines):
                    cv2.putText(frame, text, (10, 30 + i * 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            return frame

        except Exception as e:
            print(f"Erro na visualização: {e}")
            return frame

    def cleanup(self):
        """Limpar recursos"""
        if self.cap:
            self.cap.release()
            print("🛑 Câmera de detecção de linha liberada")

def main():
    """Função principal para teste"""
    print("🎯 TESTE DO DETECTOR DE LINHA PRETA")
    print("=" * 40)

    # Criar detector
    detector = LineDetector(camera_id=0)

    # Inicializar
    if not detector.initialize():
        return

    try:
        print("Pressione 'q' para sair, 'r' para resetar PID")
        print("A câmera inferior deve estar apontada para o chão")

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
                cv2.imshow("Detector de Linha Preta", vis_frame)

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
        print(f"   Sistema de detecção de linha testado")

if __name__ == "__main__":
    main()