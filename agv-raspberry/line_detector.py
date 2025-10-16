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
import os
try:
    # Tenta obter configuração padrão da câmera do config.py
    from config import HARDWARE_CONFIG
    DEFAULT_CAM_INDEX = HARDWARE_CONFIG.get('camera', {}).get('device', 0)
except Exception:
    DEFAULT_CAM_INDEX = 0

# Importar CameraManager para evitar conflitos
try:
    from qr_reader_opencv_only import get_camera_manager
    CAMERA_MANAGER_AVAILABLE = True
    print("CameraManager importado com sucesso")
except ImportError as e:
    CAMERA_MANAGER_AVAILABLE = False
    print(f"❌ Falha ao importar CameraManager: {e}")

class LineDetector:
    """Detector de linha preta usando Picamera2"""

    def __init__(self, width=None, height=None, camera_index=None):
        # Ler resolução do config se não fornecida
        try:
            cfg_res = HARDWARE_CONFIG.get('camera', {}).get('resolution', (720, 1024))
        except Exception:
            cfg_res = (720, 1024)
        self.width = width or int(cfg_res[0])
        self.height = height or int(cfg_res[1])
        self.picam2 = None
        self.camera_controls = None  # Controles de exposição/ganho a aplicar após iniciar
        # Permitir selecionar câmera por parâmetro, variável de ambiente ou config padrão
        env_idx = os.getenv('CAMERA_INDEX')
        self.camera_index = (
            int(camera_index)
            if camera_index is not None
            else (int(env_idx) if env_idx is not None and env_idx.isdigit() else 1)  # Usar câmera 1
        )

        # Configurações de processamento de imagem - MAIS TOLERANTE PARA DIFERENTES CONDIÇÕES DE ILUMINAÇÃO
        self.lower_black = np.array([0, 0, 0])
        self.upper_black = np.array([180, 255, 200])  # Muito mais tolerante - detecta pixels mais claros como pretos

        # Configurações de detecção de linha - MAIS TOLERANTE PARA DIFERENTES CONDIÇÕES
        self.min_line_width = 2   # Largura mínima muito pequena
        self.max_line_width = 800 # Maior largura máxima
        self.max_qr_width = 600  # Largura máxima para QR codes
        self.line_center_offset = 0  # Offset do centro da linha

        # ROI (Region of Interest) - área inferior da imagem (configurável)
        try:
            roi_start_frac = HARDWARE_CONFIG.get('camera', {}).get('roi_y_start_frac', 0.3)
        except Exception:
            roi_start_frac = 0.3
        self.roi_y_start = int(self.height * float(roi_start_frac))  # 30% inferior por padrão (mais área visível)
        self.roi_height = self.height - self.roi_y_start

        # PID para controle de direção
        self.kp = 0.8  # ganho maior para resposta mais rápida
        self.ki = 0.0
        self.kd = 0.12
        self.previous_error = 0
        self.integral = 0

        # Estado da linha
        self.line_detected = False
        self.line_center = self.width // 2
        self.line_width = 0
        self.line_confidence = 0

    def initialize(self):
        """Inicializar câmera usando CameraManager para evitar conflitos"""
        print("Inicializando Picamera2 para deteccao de linha...")
        print(f"Indice de camera solicitado: {self.camera_index}")

        if CAMERA_MANAGER_AVAILABLE:
            # Usar CameraManager para evitar conflitos
            self.camera_manager = get_camera_manager(self.camera_index)
            success = self.camera_manager.initialize()
            if success:
                print("✅ Picamera2 inicializada para detecção de linha!")
                return True
            else:
                print("Falha na inicializacao do Camera Manager")
                return False
        else:
            # Fallback para inicialização direta (não recomendado)
            print("⚠️ CameraManager não disponível, usando inicialização direta")
            if PICAMERA2_AVAILABLE:
                try:
                    self.picam2 = Picamera2(self.camera_index)
                    config = self.picam2.create_still_configuration(
                        main={"format": 'RGB888', "size": (self.width, self.height)}
                    )
                    self.picam2.configure(config)
                    print("✅ Picamera2 inicializada (fallback)!")
                    return True
                except Exception as e:
                    print(f"❌ Erro ao inicializar Picamera2: {e}")
                    return False
            else:
                print("❌ Picamera2 não disponível")
                return False

    def capture_frame(self):
        """Capturar frame da câmera sob demanda"""
        if CAMERA_MANAGER_AVAILABLE and hasattr(self, 'camera_manager'):
            # Usar CameraManager para evitar conflitos
            return self.camera_manager.capture_frame()
        elif PICAMERA2_AVAILABLE and self.picam2 is not None:
            # Fallback para modo direto
            try:
                # Iniciar câmera se não estiver rodando
                if not self.picam2.started:
                    self.picam2.start()
                    time.sleep(0.1)  # Pequena pausa para estabilizar
                    # Aplicar controles após iniciar
                    if self.camera_controls:
                        try:
                            self.picam2.set_controls(self.camera_controls)
                            # Pequena espera para exposição estabilizar
                            time.sleep(0.05)
                        except Exception as e:
                            print(f"⚠️ Falha ao aplicar controles: {e}")

                # Capturar frame
                frame = self.picam2.capture_array()

                # Parar câmera imediatamente para liberar recursos
                self.picam2.stop()

                return frame

            except Exception as e:
                print(f"❌ Erro ao capturar frame: {e}")
                try:
                    if self.picam2.started:
                        self.picam2.stop()
                except:
                    pass
                return None
        else:
            return None

    def preprocess_image(self, frame):
        """Pré-processar imagem para detecção de linha.
        Retorna (mask, roi, frame_bgr).
        """
        try:
            # Picamera2 capture_array retorna RGB; OpenCV usa BGR
            # Converter RGB -> BGR corretamente
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Recortar ROI (apenas área inferior) - alinhado com a resolução nova
            y1 = max(0, min(self.height - 1, self.roi_y_start))
            y2 = max(y1 + 1, min(self.height, self.roi_y_start + self.roi_height))
            roi = frame_bgr[y1:y2, :]

            # Converter para HSV a partir de BGR
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # Aplicar filtro de cor para detectar preto
            mask = cv2.inRange(hsv, self.lower_black, self.upper_black)

            # Aplicar operações morfológicas para limpar ruído
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            return mask, roi, frame_bgr

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

            # Verificar se é uma linha válida - MAIS TOLERANTE PARA QR CODES
            if w < self.min_line_width:
                print(f"Debug: Linha muito fina (w={w} < {self.min_line_width})")
                self.line_detected = False
                return False

            # Verificar se pode ser um QR code (muito largo)
            aspect_ratio = w / h if h > 0 else 10
            is_probably_qr = w > self.max_qr_width and aspect_ratio < 2.0  # QR codes são mais quadrados

            if w > self.max_line_width and not is_probably_qr:
                print(f"Debug: Linha muito larga (w={w} > {self.max_line_width}) e não parece QR")
                self.line_detected = False
                return False

            if is_probably_qr:
                print(f"Debug: Detectado possível QR code (w={w}, h={h}, ratio={aspect_ratio:.2f}) - usando centro da imagem")
                # Para QR codes, usar o centro da imagem como referência
                line_center = self.width // 2
                line_width = min(w, self.max_line_width)  # Limitar largura
                confidence = 0.5  # Confiança reduzida para QR codes
            else:
                # Cálculo normal para linhas
                line_center = x + w // 2
                line_width = w
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
            if frame is None:
                frame = self.capture_frame()

            if frame is None:
                return None

            # Pré-processar
            mask, roi, frame_bgr = self.preprocess_image(frame)
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
            info['frame_bgr'] = frame_bgr  # frame completo em BGR para usos futuros (ex.: snapshots/verde)
            info['debug_black_ratio'] = black_ratio

            return info

        except Exception as e:
            print(f"❌ Erro no processamento de frame: {e}")
            return None

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

    def start_continuous_capture(self):
        """Iniciar captura contínua para sessões de calibração/visualização"""
        if not PICAMERA2_AVAILABLE or self.picam2 is None:
            return False

        try:
            if not self.picam2.started:
                self.picam2.start()
                time.sleep(0.2)  # Pausa maior para estabilizar
                # Aplicar controles após iniciar
                if self.camera_controls:
                    try:
                        self.picam2.set_controls(self.camera_controls)
                        time.sleep(0.05)
                    except Exception as e:
                        print(f"⚠️ Falha ao aplicar controles (contínuo): {e}")
                print("📷 Câmera iniciada para captura contínua")
            return True
        except Exception as e:
            print(f"❌ Erro ao iniciar captura contínua: {e}")
            return False

    def stop_continuous_capture(self):
        """Parar captura contínua"""
        if not PICAMERA2_AVAILABLE or self.picam2 is None:
            return

        try:
            if self.picam2.started:
                self.picam2.stop()
                print("📷 Captura contínua parada")
        except Exception as e:
            print(f"❌ Erro ao parar captura contínua: {e}")

    def capture_continuous_frame(self):
        """Capturar frame durante sessão contínua (câmera já deve estar iniciada)"""
        if not PICAMERA2_AVAILABLE or self.picam2 is None:
            return None

        try:
            if not self.picam2.started:
                print("⚠️ Câmera não está ativa para captura contínua")
                return None

            frame = self.picam2.capture_array()
            return frame

        except Exception as e:
            print(f"❌ Erro ao capturar frame contínuo: {e}")
            return None

def main():
    """Função principal para teste"""
    print("🎯 TESTE DO DETECTOR DE LINHA PRETA - PICAMERA2")
    print("=" * 50)

    # CLI simples para selecionar câmera: python line_detector.py --camera 1
    cam_index = None
    try:
        if '--camera' in sys.argv:
            i = sys.argv.index('--camera')
            if i + 1 < len(sys.argv):
                cam_index = int(sys.argv[i + 1])
    except Exception:
        cam_index = None

    # Criar detector
    detector = LineDetector(camera_index=cam_index)

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
                    roi = info['roi']
                    mask = info['mask']
                    # Em vez de escurecer o ROI inteiro com a máscara, vamos apenas colorir os pixels detectados
                    overlay = roi.copy()
                    # Cor da sobreposição para pixels pretos detectados (amarelo)
                    overlay[mask == 255] = (0, 255, 255)
                    # Misturar levemente apenas nas regiões coloridas
                    combined = cv2.addWeighted(overlay, 0.35, roi, 0.65, 0)
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
