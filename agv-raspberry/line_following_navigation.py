#!/usr/bin/env python3
"""
Navegação Seguindo Linha Preta com PID
Integra detecção de linha com controle de motores e QR codes
"""

import time
import threading
import platform
from line_detector import LineDetector
from navigation_basic import BasicNavigation
from qr_reader_opencv_only import OpenCVOnlyQRReader
from config import get_esp32_port
import cv2

class LineFollowingNavigation:
    """Navegação que segue linha preta com detecção de QR codes"""

    def __init__(self, esp32_port=None, qr_camera_id=0, visual_feedback=False):
        self.esp32_port = esp32_port or get_esp32_port()

        # Componentes
        self.line_detector = LineDetector()  # Picamera2 não usa camera_id
        self.basic_nav = BasicNavigation(esp32_port=self.esp32_port)
        self.qr_detector = OpenCVOnlyQRReader(camera_id=qr_camera_id)

        # Estado da navegação
        self.following_line = False
        self.speed_base = 55  # Velocidade base ajustada para correção gradual
        self.speed_min = 25   # Velocidade mínima
        self.speed_max = 75   # Velocidade máxima

        # Detecção de QR codes
        self.qr_detected_recently = False

        # Feedback visual opcional
        self.visual_feedback = visual_feedback
        self.visual_window_name = "AGV - Seguimento de Linha"
        self.current_frame = None
        self.status_info = {
            'velocidade': 0,
            'direcao': 'parado',
            'erro_pixels': 0,
            'correcao': 0.0,
            'qr_detectado': False,
            'linha_detectada': False,
            'confianca': 0.0
        }

    def enable_visual_feedback(self):
        """Ativar feedback visual"""
        self.visual_feedback = True
        print("👁️ Feedback visual ativado")

    def disable_visual_feedback(self):
        """Desativar feedback visual"""
        self.visual_feedback = False
        try:
            cv2.destroyWindow(self.visual_window_name)
        except:
            pass
        print("👁️ Feedback visual desativado")

    def update_visual_frame(self, frame, line_info=None):
        """Atualizar frame para display visual"""
        if not self.visual_feedback or frame is None:
            return

        self.current_frame = frame.copy()

        # Desenhar informações na imagem
        height, width = self.current_frame.shape[:2]

        # Desenhar linha central da imagem
        cv2.line(self.current_frame, (width//2, 0), (width//2, height), (255, 255, 255), 1)

        # Desenhar ROI (área de detecção)
        roi_y_start = int(height * 0.4)
        cv2.rectangle(self.current_frame, (0, roi_y_start), (width, height), (0, 255, 0), 2)

        # Desenhar linha detectada
        if line_info and line_info.get('detected', False):
            center = line_info.get('center', width//2)
            width_line = line_info.get('width', 0)

            # Linha central detectada
            cv2.circle(self.current_frame, (center, height//2), 5, (0, 255, 0), -1)

            # Bounding box da linha
            if 'x' in line_info and 'w' in line_info:
                x, y, w, h = line_info['x'], line_info['y'], line_info['w'], line_info['h']
                cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Adicionar texto de status
        self._draw_status_text()

        # Mostrar imagem
        cv2.imshow(self.visual_window_name, self.current_frame)
        cv2.waitKey(1)  # Necessário para atualizar a janela

    def _draw_status_text(self):
        """Desenhar texto de status na imagem"""
        if self.current_frame is None:
            return

        # Informações de status
        status_lines = [
            f"Velocidade: {self.status_info['velocidade']}",
            f"Direcao: {self.status_info['direcao']}",
            f"Erro: {self.status_info['erro_pixels']}px",
            f"Correcao: {self.status_info['correcao']:.3f}",
            f"Linha: {'Sim' if self.status_info['linha_detectada'] else 'Nao'}",
            f"QR: {'Sim' if self.status_info['qr_detectado'] else 'Nao'}",
            f"Confiança: {self.status_info['confianca']:.2f}"
        ]

        # Desenhar fundo semi-transparente
        overlay = self.current_frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 25*len(status_lines)+10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, self.current_frame, 0.3, 0, self.current_frame)

        # Desenhar texto
        for i, line in enumerate(status_lines):
            cv2.putText(self.current_frame, line, (20, 35 + i*25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Controle PID para direção (removido - usando o do LineDetector)
        # self.kp = 0.5
        # self.ki = 0.0
        # self.kd = 0.1
        # self.previous_error = 0
        # self.integral = 0

        # Detecção de interseções
        self.intersection_detected = False
        self.intersection_timeout = 3.0  # Tempo para confirmar interseção

        # Threading
        self.navigation_thread = None
        self.stop_event = threading.Event()

    def initialize(self):
        """Inicializar todos os componentes"""
        print("INICIALIZANDO NAVEGAÇÃO SEGUINDO LINHA")
        print("=" * 45)

        success = True
        system = platform.system().lower()

        # Inicializar navegação básica (pode falhar no Windows sem ESP32)
        if not self.basic_nav.inicializar():
            if system == 'windows':
                print("⚠️ ESP32 não disponível no Windows - modo simulação ativado")
                print("✅ Navegação básica em modo simulação")
            else:
                print("Falha na navegacao basica")
                success = False

        # Inicializar detector de linha
        if not self.line_detector.initialize():
            print("❌ Falha no detector de linha")
            success = False

        # Inicializar detector QR (opcional)
        if not self.qr_detector.initialize():
            print("⚠️ Detector QR não disponível - funcionando sem QR")

        if success:
            print("✅ Navegação seguindo linha inicializada!")
            if system == 'windows':
                print("💡 Modo Windows: Use para testes visuais e simulação")
        else:
            print("❌ Falha na inicialização")

        return success

    def calculate_motor_speeds(self, steering_correction):
        """Calcular velocidades dos motores baseado na correção de direção (LEGACY - não usado)"""
        # Este método não é mais usado pois o controle é feito via comandos do ESP32
        correction = steering_correction * self.steering_sensitivity
        left_speed = self.speed_base - (correction * (self.speed_base - self.speed_min))
        right_speed = self.speed_base + (correction * (self.speed_base - self.speed_min))
        left_speed = max(self.speed_min, min(self.speed_max, left_speed))
        right_speed = max(self.speed_min, min(self.speed_max, right_speed))
        return int(left_speed), int(right_speed)

    def follow_line_step(self):
        """Executar um passo de seguimento de linha com detecção de QR codes"""
        try:
            # Detectar linha
            line_info = self.line_detector.process_frame()

            if not line_info or not line_info['detected']:
                print("⚠️ Linha não detectada - parando")
                self.status_info.update({
                    'velocidade': 0,
                    'direcao': 'parado',
                    'linha_detectada': False,
                    'qr_detectado': False
                })
                self.update_visual_frame(None, line_info)
                
                # Só parar motores se ESP32 estiver disponível
                if hasattr(self.basic_nav, 'mpu') and self.basic_nav.mpu.serial_conn:
                    self.basic_nav.parar()
                return False

            # Obter correção de direção calculada pelo detector
            steering_correction = line_info['steering_correction']
            error_pixels = line_info['center'] - (self.line_detector.width // 2)

            print(f"📏 Centro linha: {line_info['center']}, Erro: {error_pixels}px, Correção: {steering_correction:.3f}")

            # Verificar se pode ser um QR code (linha muito larga)
            is_qr_detection = line_info['width'] > self.line_detector.max_qr_width

            # Atualizar status
            direcao = 'frente'
            velocidade = self.speed_base

            # Só enviar comandos se ESP32 estiver disponível
            esp32_available = hasattr(self.basic_nav, 'mpu') and self.basic_nav.mpu.serial_conn is not None

            if is_qr_detection:
                print("🔳 Detectado possível QR code - reduzindo velocidade para leitura")
                # Reduzir velocidade quando detecta possível QR code
                velocidade = max(20, self.speed_base // 2)
                direcao = 'frente_lento'
                if esp32_available:
                    self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': velocidade})
                # Definir flag para loop mais lento
                self.qr_detected_recently = True
            else:
                self.qr_detected_recently = False

                # Correção gradual: pequenas correções intercaladas com movimento para frente
                base_speed = self.speed_base

                if abs(steering_correction) < 0.05:
                    # Movimento reto normal - manter por mais tempo
                    print("➡️ Movimento reto")
                    direcao = 'frente'
                    velocidade = base_speed
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                elif abs(steering_correction) < 0.3:
                    # Correção leve - movimento para frente com velocidade reduzida
                    reduced_speed = max(self.speed_min, base_speed - int(abs(steering_correction) * 10))
                    print(f"🔄 Correção leve ({steering_correction:.3f}) - velocidade reduzida: {reduced_speed}")
                    direcao = 'frente_corrigido'
                    velocidade = reduced_speed
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': reduced_speed})
                else:
                    # Correção necessária - impulso de correção muito suave seguido de movimento para frente
                    # INVERTER A DIREÇÃO: steering_correction > 0 significa linha à direita, então virar para ESQUERDA
                    correction_speed = max(3, min(8, int(abs(steering_correction) * 6)))  # Velocidade ainda menor

                    if steering_correction > 0:
                        # Linha à direita - virar para ESQUERDA (invertido)
                        print(f"↪️ Correção esquerda suave (impulso: {correction_speed})")
                        direcao = 'corrigindo_esquerda'
                        velocidade = correction_speed
                        if esp32_available:
                            self.basic_nav.mpu.enviar_comando('virar_esquerda', {'velocidade': correction_speed})
                    else:
                        # Linha à esquerda - virar para DIREITA (invertido)
                        print(f"↩️ Correção direita suave (impulso: {correction_speed})")
                        direcao = 'corrigindo_direita'
                        velocidade = correction_speed
                        if esp32_available:
                            self.basic_nav.mpu.enviar_comando('virar_direita', {'velocidade': correction_speed})

                    # Imediatamente voltar ao movimento para frente
                    if esp32_available:
                        time.sleep(0.03)  # Tempo ainda menor para correção mais suave
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                    direcao = 'frente_apos_correcao'
                    velocidade = base_speed

            # Atualizar informações de status
            self.status_info.update({
                'velocidade': velocidade,
                'direcao': direcao,
                'erro_pixels': error_pixels,
                'correcao': steering_correction,
                'qr_detectado': is_qr_detection,
                'linha_detectada': True,
                'confianca': line_info.get('confidence', 0.0)
            })

            # Atualizar display visual
            self.update_visual_frame(line_info.get('roi'), line_info)

            return True

        except Exception as e:
            print(f"❌ Erro no seguimento de linha: {e}")
            self.status_info.update({
                'velocidade': 0,
                'direcao': 'erro',
                'linha_detectada': False
            })
            self.update_visual_frame(None)
            self.basic_nav.parar()
            return False

    def detect_intersection(self):
        """Detectar interseção na linha (formato T)"""
        try:
            # Verificar se há expansão da linha (interseção)
            line_info = self.line_detector.process_frame()

            if line_info and line_info['detected']:
                # Se a linha ficou muito larga, pode ser interseção
                if line_info['width'] > self.line_detector.max_line_width * 1.5:
                    if not self.intersection_detected:
                        self.intersection_detected = True
                        print("🔀 Interseção detectada!")
                        return True
                else:
                    self.intersection_detected = False

            return self.intersection_detected

        except Exception as e:
            print(f"Erro na detecção de interseção: {e}")
            return False

    def check_qr_codes(self):
        """Verificar QR codes durante a navegação"""
        try:
            qr_result = self.qr_detector.detectar_qr_code()

            if qr_result and qr_result['detectado']:
                qr_code = qr_result['codigo']
                print(f"📷 QR code detectado durante navegação: {qr_code}")

                # Verificar se é um QR code de subcorredor
                if qr_code.startswith('Corredor') and '_' in qr_code:
                    return qr_code

            return None

        except Exception as e:
            print(f"Erro na verificação de QR codes: {e}")
            return None

    def navigate_to_intersection(self, target_subcorredor):
        """Navegar até encontrar a interseção do subcorredor alvo"""
        print(f"🎯 Navegando até interseção do subcorredor: {target_subcorredor}")

        start_time = time.time()
        qr_found = None

        while not self.stop_event.is_set():
            # Seguir linha
            if not self.follow_line_step():
                break

            # Verificar interseção
            if self.detect_intersection():
                print("🔀 Interseção encontrada!")

                # Verificar QR code na interseção
                qr_found = self.check_qr_codes()

                if qr_found and qr_found == f"Corredor01_{target_subcorredor}":
                    print(f"✅ Subcorredor correto encontrado: {qr_found}")
                    break
                else:
                    print(f"⚠️ Subcorredor errado ou QR não encontrado: {qr_found}")
                    # Continuar procurando

            # Timeout
            if time.time() - start_time > 30:  # 30 segundos máximo
                print("⏰ Timeout na navegação até interseção")
                break

            time.sleep(0.1)

        return qr_found

    def enter_subcorredor(self):
        """Entrar no subcorredor após encontrar a interseção"""
        print("➡️ Entrando no subcorredor")

        # Virar 90° para direita (assumindo layout em T)
        if not self.basic_nav.virar_90_graus('direita'):
            return False

        # Seguir em frente por uma distância
        distance_to_shelf = 30  # cm até a prateleira
        if not self.basic_nav.mover_em_linha_reta(distance_to_shelf, 'frente'):
            return False

        print("✅ Entrada no subcorredor concluída")
        return True

    def exit_subcorredor(self):
        """Sair do subcorredor de volta à linha principal"""
        print("⬅️ Saindo do subcorredor")

        # Dar ré até a linha principal
        if not self.basic_nav.mover_em_linha_reta(30, 'tras'):
            return False

        # Virar 90° para esquerda para voltar à linha
        if not self.basic_nav.virar_90_graus('esquerda'):
            return False

        print("✅ Saída do subcorredor concluída")
        return True

    def navigate_to_delivery_point(self):
        """Navegar até o ponto de entrega"""
        print("📦 Navegando até ponto de entrega")

        qr_delivery = "Entrega"
        start_time = time.time()

        while not self.stop_event.is_set():
            # Seguir linha
            if not self.follow_line_step():
                break

            # Verificar QR code de entrega
            qr_found = self.check_qr_codes()
            if qr_found == qr_delivery:
                print("✅ Ponto de entrega encontrado!")
                return True

            # Timeout
            if time.time() - start_time > 60:  # 1 minuto máximo
                print("⏰ Timeout na navegação até entrega")
                break

            time.sleep(0.1)

        return False

    def start_line_following(self):
        """Iniciar seguimento de linha em thread separada"""
        if self.following_line:
            print("⚠️ Seguimento de linha já ativo")
            return

        self.stop_event.clear()
        self.following_line = True

        self.navigation_thread = threading.Thread(target=self._line_following_loop)
        self.navigation_thread.daemon = True
        self.navigation_thread.start()

        print("▶️ Seguimento de linha iniciado")

    def stop_line_following(self):
        """Parar seguimento de linha"""
        if not self.following_line:
            return

        self.stop_event.set()
        self.following_line = False

        if self.navigation_thread:
            self.navigation_thread.join(timeout=2)

        self.basic_nav.parar()

        # Fechar janela visual se estiver aberta
        if self.visual_feedback:
            try:
                cv2.destroyWindow(self.visual_window_name)
            except:
                pass

        print("⏹️ Seguimento de linha parado")

    def _line_following_loop(self):
        """Loop principal de seguimento de linha com timing adaptativo"""
        print("🔄 Iniciando loop de seguimento de linha")

        while not self.stop_event.is_set():
            try:
                success = self.follow_line_step()
                if success:
                    # Timing adaptativo baseado na detecção de QR
                    if self.qr_detected_recently:
                        time.sleep(0.5)  # Mais lento quando detecta QR recentemente
                    else:
                        time.sleep(0.15)  # Normal
                else:
                    time.sleep(0.3)  # Pausa maior se não detectar linha

            except Exception as e:
                print(f"Erro no loop de seguimento: {e}")
                break

        print("🔄 Loop de seguimento finalizado")

    def test_line_following(self, duration=10):
        """Testar seguimento de linha por tempo determinado"""
        print(f"🧪 Testando seguimento de linha por {duration} segundos")

        self.start_line_following()
        time.sleep(duration)
        self.stop_line_following()

        print("✅ Teste concluído")

    def cleanup(self):
        """Limpar recursos"""
        self.stop_line_following()
        self.line_detector.cleanup()
        # QR detector não tem cleanup
        print("🧹 Recursos de navegação liberados")

def main():
    """Função principal para teste"""
    print("NAVEGACAO SEGUINDO LINHA PRETA")
    print("=" * 35)

    # Criar navegação
    nav = LineFollowingNavigation()

    # Inicializar
    if not nav.initialize():
        return

    # Menu de teste
    while True:
        print("\n" + "="*50)
        print("🎮 MENU DE NAVEGAÇÃO POR LINHA")
        print("="*50)
        print("1. Teste básico de seguimento (10s)")
        print("2. Navegar até subcorredor 01")
        print("3. Entrar no subcorredor")
        print("4. Sair do subcorredor")
        print("5. Ir para ponto de entrega")
        print("6. Mostrar status")
        print("7. Parar motores")
        print("8. Ativar feedback visual")
        print("9. Desativar feedback visual")
        print("0. Sair")
        print("="*50)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                nav.test_line_following(10)
            elif opcao == '2':
                nav.navigate_to_intersection("01")
            elif opcao == '3':
                nav.enter_subcorredor()
            elif opcao == '4':
                nav.exit_subcorredor()
            elif opcao == '5':
                nav.navigate_to_delivery_point()
            elif opcao == '6':
                nav.basic_nav.mostrar_status()
            elif opcao == '7':
                nav.basic_nav.parar()
                print("🛑 Motores parados")
            elif opcao == '8':
                nav.enable_visual_feedback()
            elif opcao == '9':
                nav.disable_visual_feedback()
            elif opcao == '0':
                nav.cleanup()
                print("👋 Saindo...")
                break
            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            nav.cleanup()
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            nav.cleanup()

if __name__ == "__main__":
    main()