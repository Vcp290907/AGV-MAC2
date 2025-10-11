#!/usr/bin/env python3
"""
Teste de Detecção de Linha Preta + QR Codes
Sistema visual básico para AGV - apenas câmera e detecção
"""

import cv2
import numpy as np
from picamera2 import Picamera2
from pyzbar import pyzbar
import time

class LineQRDetector:
    """Detector de linha preta e QR codes"""

    def __init__(self):
        self.picam2 = None
        self.qr_codes_detectados = set()

        # Configurações de detecção de linha
        self.kernel_size = 5
        self.low_threshold = 50
        self.high_threshold = 150

        # Configurações de cor para linha preta
        self.black_lower = np.array([0, 0, 0])
        self.black_upper = np.array([180, 255, 50])

    def initialize_camera(self):
        """Inicializar câmera CSI"""
        print("📷 Inicializando câmera CSI para teste visual...")

        try:
            self.picam2 = Picamera2(camera_num=0)
            self.picam2.configure(self.picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (1280, 720)}
            ))
            self.picam2.start()
            print("✅ Câmera CSI inicializada!")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar câmera: {e}")
            return False

    def detectar_linha_preta(self, frame):
        """Detectar linha preta na imagem"""
        try:
            # Converter para HSV para melhor detecção de cor
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Criar máscara para cor preta
            mask = cv2.inRange(hsv, self.black_lower, self.black_upper)

            # Aplicar operações morfológicas para limpar a máscara
            kernel = np.ones((self.kernel_size, self.kernel_size), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            linha_detectada = False
            centro_linha = None

            if contours:
                # Encontrar o maior contorno (provavelmente a linha)
                maior_contorno = max(contours, key=cv2.contourArea)

                if cv2.contourArea(maior_contorno) > 500:  # Área mínima
                    linha_detectada = True

                    # Calcular centro da linha
                    M = cv2.moments(maior_contorno)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        centro_linha = (cx, cy)

                        # Desenhar contorno e centro
                        cv2.drawContours(frame, [maior_contorno], -1, (0, 255, 0), 3)
                        cv2.circle(frame, centro_linha, 5, (0, 0, 255), -1)

            return linha_detectada, centro_linha, mask

        except Exception as e:
            print(f"❌ Erro na detecção de linha: {e}")
            return False, None, None

    def detectar_qr_codes(self, frame):
        """Detectar QR codes na imagem"""
        try:
            # Converter para escala de cinza
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Aplicar CLAHE para melhorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)

            # Detectar QR codes
            decoded_objects = pyzbar.decode(enhanced)

            qr_info = []
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                qr_info.append({
                    'data': data,
                    'bbox': obj.rect,
                    'type': obj.type
                })

                # Desenhar retângulo
                (x, y, w, h) = obj.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Mostrar texto
                cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            return qr_info

        except Exception as e:
            print(f"❌ Erro na detecção de QR: {e}")
            return []

    def mostrar_status(self, frame, linha_detectada, centro_linha, qr_codes):
        """Mostrar status na tela"""
        height, width = frame.shape[:2]

        # Status da linha
        if linha_detectada:
            status_linha = "✅ LINHA DETECTADA"
            cor_linha = (0, 255, 0)
        else:
            status_linha = "❌ Linha não detectada"
            cor_linha = (0, 0, 255)

        # Status dos QR codes
        if qr_codes:
            status_qr = f"🎯 QR DETECTADO: {qr_codes[0]['data']}"
            cor_qr = (255, 0, 0)
        else:
            status_qr = "Aguardando QR code..."
            cor_qr = (255, 255, 255)

        # Desenhar informações na tela
        cv2.putText(frame, status_linha, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, cor_linha, 2)
        cv2.putText(frame, status_qr, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_qr, 2)

        # Centro da linha
        if centro_linha:
            cv2.putText(frame, f"Centro: {centro_linha}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Contador de QR únicos
        cv2.putText(frame, f"QR únicos: {len(self.qr_codes_detectados)}", (10, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Instruções
        cv2.putText(frame, "Q: Sair | R: Reset QR", (width - 250, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    def executar_teste(self):
        """Executar teste visual completo"""
        print("🧪 TESTE VISUAL: LINHA PRETA + QR CODES")
        print("=" * 45)
        print("Este teste mostra apenas detecção visual")
        print("Pressione 'q' para sair, 'r' para resetar QR codes")
        print()

        if not self.initialize_camera():
            return

        try:
            while True:
                # Capturar frame
                frame = self.picam2.capture_array()

                # Detectar linha preta
                linha_detectada, centro_linha, mask_linha = self.detectar_linha_preta(frame)

                # Detectar QR codes
                qr_codes = self.detectar_qr_codes(frame)

                # Registrar QR codes únicos
                for qr in qr_codes:
                    if qr['data'] not in self.qr_codes_detectados:
                        self.qr_codes_detectados.add(qr['data'])
                        print(f"🎯 Novo QR detectado: {qr['data']}")

                # Mostrar status na tela
                self.mostrar_status(frame, linha_detectada, centro_linha, qr_codes)

                # Mostrar máscara da linha em uma janela separada (opcional)
                if mask_linha is not None:
                    # Redimensionar máscara para ficar do mesmo tamanho
                    mask_resized = cv2.resize(mask_linha, (320, 180))
                    cv2.imshow("Mascara Linha Preta", mask_resized)

                # Mostrar frame principal
                cv2.imshow("Teste Visual AGV: Linha + QR", frame)

                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.qr_codes_detectados.clear()
                    print("🔄 Lista de QR codes resetada")

                time.sleep(0.05)  # Pequena pausa

        except KeyboardInterrupt:
            print("\n🛑 Teste interrompido")

        finally:
            cv2.destroyAllWindows()
            if self.picam2:
                self.picam2.stop()

            # Resumo final
            print(f"\n📊 RESUMO DO TESTE:")
            print(f"   Linha preta: Sistema de detecção ativo")
            print(f"   QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   QR codes detectados:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 TESTE VISUAL AGV")
    print("=" * 20)
    print("Teste de detecção de linha preta e QR codes")
    print("Ideal para validar o sistema de visão")

    # Criar detector
    detector = LineQRDetector()

    # Executar teste
    detector.executar_teste()

if __name__ == "__main__":
    main()