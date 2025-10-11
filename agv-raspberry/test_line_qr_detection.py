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

        # Configurações de cor para linha preta (HSV)
        self.black_lower = np.array([0, 0, 0])
        self.black_upper = np.array([180, 255, 50])

        # Parâmetros ajustáveis em tempo real
        self.modo_config = False
        self.param_atual = 0
        self.parametros = [
            {'nome': 'Hue Min', 'valor': 0, 'min': 0, 'max': 180, 'step': 5},
            {'nome': 'Hue Max', 'valor': 180, 'min': 0, 'max': 180, 'step': 5},
            {'nome': 'Sat Min', 'valor': 0, 'min': 0, 'max': 255, 'step': 10},
            {'nome': 'Sat Max', 'valor': 255, 'min': 0, 'max': 255, 'step': 10},
            {'nome': 'Val Min', 'valor': 0, 'min': 0, 'max': 255, 'step': 10},
            {'nome': 'Val Max', 'valor': 70, 'min': 0, 'max': 255, 'step': 5},
            {'nome': 'Area Min', 'valor': 500, 'min': 100, 'max': 5000, 'step': 100},
            {'nome': 'Kernel Size', 'valor': 5, 'min': 3, 'max': 15, 'step': 2},
            {'nome': 'Linha Horizontal', 'valor': 360, 'min': 50, 'max': 670, 'step': 10}
        ]

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

    def atualizar_parametros(self):
        """Atualizar parâmetros da detecção baseado nos valores ajustáveis"""
        self.black_lower = np.array([
            self.parametros[0]['valor'],  # Hue Min
            self.parametros[2]['valor'],  # Sat Min
            self.parametros[4]['valor']   # Val Min
        ])

        self.black_upper = np.array([
            self.parametros[1]['valor'],  # Hue Max
            self.parametros[3]['valor'],  # Sat Max
            self.parametros[5]['valor']   # Val Max
        ])

        self.area_minima = self.parametros[6]['valor']
        self.kernel_size = self.parametros[7]['valor']
        # Linha horizontal é usada diretamente nos métodos

    def detectar_linha_preta(self, frame):
        """Detectar linha preta na imagem com parâmetros ajustáveis"""
        try:
            # Atualizar parâmetros se estiver em modo config
            if self.modo_config:
                self.atualizar_parametros()

            # Obter linha horizontal de corte
            linha_horizontal = self.parametros[8]['valor']
            height, width = frame.shape[:2]

            # Criar região de interesse (apenas abaixo da linha horizontal)
            roi = frame[linha_horizontal:height, 0:width]

            # Converter para HSV para melhor detecção de cor
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

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

                if cv2.contourArea(maior_contorno) > self.area_minima:
                    linha_detectada = True

                    # Calcular centro da linha (ajustar coordenadas para frame completo)
                    M = cv2.moments(maior_contorno)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"]) + linha_horizontal  # Ajustar para coordenada completa
                        centro_linha = (cx, cy)

                        # Desenhar contorno e centro no frame completo
                        # Ajustar contorno para coordenadas do frame completo
                        contorno_ajustado = maior_contorno + np.array([0, linha_horizontal])
                        cv2.drawContours(frame, [contorno_ajustado], -1, (0, 255, 0), 3)
                        cv2.circle(frame, centro_linha, 5, (0, 0, 255), -1)

            return linha_detectada, centro_linha, mask

        except Exception as e:
            print(f"❌ Erro na detecção de linha: {e}")
            return False, None, None

    def detectar_qr_codes(self, frame):
        """Detectar QR codes na imagem (apenas abaixo da linha horizontal)"""
        try:
            # Obter linha horizontal de corte
            linha_horizontal = self.parametros[8]['valor']
            height, width = frame.shape[:2]

            # Criar região de interesse (apenas abaixo da linha horizontal)
            roi = frame[linha_horizontal:height, 0:width]

            # Converter para escala de cinza
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # Aplicar CLAHE para melhorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)

            # Detectar QR codes
            decoded_objects = pyzbar.decode(enhanced)

            qr_info = []
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')

                # Ajustar coordenadas do bbox para o frame completo
                (x, y, w, h) = obj.rect
                bbox_ajustado = (x, y + linha_horizontal, w, h)

                qr_info.append({
                    'data': data,
                    'bbox': bbox_ajustado,
                    'type': obj.type
                })

                # Desenhar retângulo no frame completo
                cv2.rectangle(frame, (x, y + linha_horizontal), (x + w, y + h + linha_horizontal), (255, 0, 0), 2)

                # Mostrar texto
                cv2.putText(frame, data, (x, y + linha_horizontal - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            return qr_info

        except Exception as e:
            print(f"❌ Erro na detecção de QR: {e}")
            return []

    def mostrar_menu_config(self, frame):
        """Mostrar menu de configuração na tela"""
        height, width = frame.shape[:2]

        # Fundo semi-transparente para o menu
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width-10, height-10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Título
        cv2.putText(frame, "CONFIGURACAO DETECCAO LINHA", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

        # Mostrar parâmetros
        y_pos = 100
        for i, param in enumerate(self.parametros):
            cor = (0, 255, 0) if i == self.param_atual else (255, 255, 255)
            indicador = ">>>" if i == self.param_atual else "   "

            texto = f"{indicador} {param['nome']}: {param['valor']}"
            cv2.putText(frame, texto, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
            y_pos += 40

        # Instruções
        instrucoes = [
            "SETAS CIMA/BAIXO: Navegar parametros",
            "SETAS ESQUERDA/DIREITA: Ajustar valores",
            "C: Salvar e voltar ao teste",
            "ESC: Cancelar configuracao"
        ]

        y_pos = height - 150
        for instrucao in instrucoes:
            cv2.putText(frame, instrucao, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            y_pos += 25

    def mostrar_status(self, frame, linha_detectada, centro_linha, qr_codes):
        """Mostrar status na tela"""
        height, width = frame.shape[:2]

        # Desenhar linha horizontal ajustável
        linha_horizontal = self.parametros[8]['valor']
        cv2.line(frame, (0, linha_horizontal), (width, linha_horizontal), (255, 255, 0), 2)
        cv2.putText(frame, f"Linha: {linha_horizontal}", (10, linha_horizontal - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Se estiver em modo configuração, mostrar menu
        if self.modo_config:
            self.mostrar_menu_config(frame)
            return

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

        # Parâmetros atuais
        param_info = f"H:{self.parametros[0]['valor']}-{self.parametros[1]['valor']} S:{self.parametros[2]['valor']}-{self.parametros[3]['valor']} V:{self.parametros[4]['valor']}-{self.parametros[5]['valor']}"
        cv2.putText(frame, param_info, (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        # Contador de QR únicos
        cv2.putText(frame, f"QR únicos: {len(self.qr_codes_detectados)}", (10, height - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Instruções
        cv2.putText(frame, "Q: Sair | R: Reset QR | T: Configurar", (10, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    def executar_teste(self):
        """Executar teste visual completo"""
        print("🧪 TESTE VISUAL: LINHA PRETA + QR CODES")
        print("=" * 45)
        print("Este teste mostra apenas detecção visual")
        print("Controles:")
        print("  Q: Sair")
        print("  R: Reset QR codes")
        print("  T: Entrar no modo configuração")
        print("  ESC: Sair da configuração")
        print("  C: Salvar configuração")
        print("  Setas: Navegar e ajustar parâmetros")
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

                    # Mostrar ROI (região de interesse) em outra janela
                    linha_horizontal = self.parametros[8]['valor']
                    roi_display = np.zeros((height, width), dtype=np.uint8)
                    roi_display[linha_horizontal:height, 0:width] = mask_linha
                    roi_resized = cv2.resize(roi_display, (320, 180))
                    cv2.imshow("Regiao de Interesse (ROI)", roi_resized)

                # Mostrar frame principal
                cv2.imshow("Teste Visual AGV: Linha + QR", frame)

                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.qr_codes_detectados.clear()
                    print("🔄 Lista de QR codes resetada")
                elif key == ord('t'):
                    self.modo_config = True
                    print("🔧 Entrando no modo configuração...")
                elif key == 27:  # ESC
                    if self.modo_config:
                        self.modo_config = False
                        print("❌ Configuração cancelada")
                    else:
                        break
                elif key == ord('c') and self.modo_config:
                    self.modo_config = False
                    print("✅ Configuração salva!")

                # Controles do menu de configuração
                if self.modo_config:
                    if key == 82:  # Seta cima
                        self.param_atual = (self.param_atual - 1) % len(self.parametros)
                    elif key == 84:  # Seta baixo
                        self.param_atual = (self.param_atual + 1) % len(self.parametros)
                    elif key == 81:  # Seta esquerda
                        param = self.parametros[self.param_atual]
                        param['valor'] = max(param['min'], param['valor'] - param['step'])
                        print(f"📉 {param['nome']}: {param['valor']}")
                    elif key == 83:  # Seta direita
                        param = self.parametros[self.param_atual]
                        param['valor'] = min(param['max'], param['valor'] + param['step'])
                        print(f"📈 {param['nome']}: {param['valor']}")

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
            print(f"   Linha horizontal: {self.parametros[8]['valor']} pixels")
            print(f"   QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   QR codes detectados:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")
            print(f"   Parâmetros finais:")
            for param in self.parametros:
                print(f"     {param['nome']}: {param['valor']}")

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