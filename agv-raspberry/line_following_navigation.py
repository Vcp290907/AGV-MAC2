#!/usr/bin/env python3
"""
Navegação Seguindo Linha Preta com PID
Integra detecção de linha com controle de motores e QR codes
"""

import time
import threading
from line_detector import LineDetector
from navigation_basic import BasicNavigation
from qr_reader_opencv_only import OpenCVOnlyQRReader
from config import get_esp32_port

class LineFollowingNavigation:
    """Navegação que segue linha preta com detecção de QR codes"""

    def __init__(self, esp32_port=None, qr_camera_id=0):
        self.esp32_port = esp32_port or get_esp32_port()

        # Componentes
        self.line_detector = LineDetector()  # Picamera2 não usa camera_id
        self.basic_nav = BasicNavigation(esp32_port=self.esp32_port)
        self.qr_detector = OpenCVOnlyQRReader(camera_id=qr_camera_id)

        # Estado da navegação
        self.following_line = False
        self.speed_base = 60  # Velocidade base (0-100)
        self.speed_min = 30   # Velocidade mínima
        self.speed_max = 80   # Velocidade máxima

        # Controle PID para direção
        self.steering_sensitivity = 0.3  # Sensibilidade da direção

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

        # Inicializar navegação básica
        if not self.basic_nav.inicializar():
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
        else:
            print("❌ Falha na inicialização")

        return success

    def calculate_motor_speeds(self, steering_correction):
        """Calcular velocidades dos motores baseado na correção de direção"""
        # Correção de direção: -1 (esquerda) a +1 (direita)
        correction = steering_correction * self.steering_sensitivity

        # Calcular velocidades esquerda/direita
        left_speed = self.speed_base - (correction * (self.speed_base - self.speed_min))
        right_speed = self.speed_base + (correction * (self.speed_base - self.speed_min))

        # Limitar velocidades
        left_speed = max(self.speed_min, min(self.speed_max, left_speed))
        right_speed = max(self.speed_min, min(self.speed_max, right_speed))

        return int(left_speed), int(right_speed)

    def follow_line_step(self):
        """Executar um passo de seguimento de linha"""
        try:
            print("🔄 Iniciando passo de seguimento...")

            # Detectar linha
            line_info = self.line_detector.process_frame()

            if not line_info or not line_info['detected']:
                print("⚠️ Linha não detectada - parando")
                self.basic_nav.parar()
                return False

            # Calcular correção de direção
            steering_correction = line_info['steering_correction']
            print(f"📏 Correção calculada: {steering_correction:.3f}")

            # Calcular velocidades dos motores
            left_speed, right_speed = self.calculate_motor_speeds(steering_correction)
            print(f"⚙️ Velocidades: L{left_speed}/R{right_speed}")

            # Enviar comando para motores
            if abs(steering_correction) < 0.1:
                print("➡️ Movendo para frente normal")
                result = self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': self.speed_base})
                print(f"📡 Comando enviado: {result}")
            else:
                print("🔄 Aplicando correção de direção")
                if steering_correction > 0:
                    result = self.basic_nav.mpu.enviar_comando('virar_direita', {'velocidade': 30})
                    print(f"📡 Comando virar_direita enviado: {result}")
                else:
                    result = self.basic_nav.mpu.enviar_comando('virar_esquerda', {'velocidade': 30})
                    print(f"📡 Comando virar_esquerda enviado: {result}")

            return True

        except Exception as e:
            print(f"❌ Erro no seguimento de linha: {e}")
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
        print("⏹️ Seguimento de linha parado")

    def _line_following_loop(self):
        """Loop principal de seguimento de linha"""
        print("🔄 Iniciando loop de seguimento de linha")

        while not self.stop_event.is_set():
            try:
                self.follow_line_step()
                time.sleep(0.1)  # 10Hz

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
        self.qr_detector.cleanup()
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