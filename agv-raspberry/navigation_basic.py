#!/usr/bin/env python3
"""
Navegação Básica do AGV
Movimento em linha reta + curvas de 90 graus usando MPU6050
"""

import time
import math
from datetime import datetime
from mpu6050_integration import MPU6050Integration
from config import get_esp32_port, get_esp32_baudrate

class BasicNavigation:
    """Navegação básica: linha reta + curvas de 90°"""

    def __init__(self, esp32_port=None):
        self.mpu = MPU6050Integration(esp32_port=esp32_port or get_esp32_port(), baudrate=get_esp32_baudrate())
        self.velocidade_base = 80  # Velocidade padrão (0-100)

        # Configurações de navegação
        self.angulo_curva = 90  # Graus para curvas
        self.tolerancia_angulo = 5  # Tolerância em graus
        self.distancia_minima = 50  # cm (simulado)

        # Estado atual
        self.posicao_atual = {'x': 0, 'y': 0, 'angulo': 0}
        self.movimento_ativo = False

    def inicializar(self):
        """Inicializar navegação"""
        print("🚀 INICIALIZANDO NAVEGAÇÃO BÁSICA")
        print("=" * 40)

        if not self.mpu.conectar_esp32():
            print("❌ Falha ao conectar ESP32")
            return False

        if not self.mpu.calibrar_sensor():
            print("❌ Falha na calibração do MPU6050")
            return False

        print("✅ Navegação inicializada!")
        return True

    def mover_em_linha_reta(self, distancia_cm, direcao='frente'):
        """Mover em linha reta por uma distância"""
        try:
            print(f"📏 Movendo em linha reta: {distancia_cm}cm para {direcao}")

            # Calcular tempo baseado na velocidade (simulação)
            # Velocidade aproximada: 20 cm/s
            tempo_movimento = distancia_cm / 20.0

            # Enviar comando de movimento
            if direcao == 'frente':
                self.mpu.enviar_comando('mover_frente', {'velocidade': self.velocidade_base})
            else:
                self.mpu.enviar_comando('mover_tras', {'velocidade': self.velocidade_base})

            # Monitorar movimento
            inicio = time.time()
            while time.time() - inicio < tempo_movimento:
                status = self.mpu.obter_status_completo()

                if status:
                    # Mostrar progresso
                    progresso = (time.time() - inicio) / tempo_movimento * 100
                    print(f"Progresso: {progresso:.1f}%")
                time.sleep(0.1)

            # Parar movimento
            self.parar()

            # Atualizar posição (simulação)
            angulo_rad = math.radians(self.posicao_atual['angulo'])
            delta_x = distancia_cm * math.cos(angulo_rad) if direcao == 'frente' else -distancia_cm * math.cos(angulo_rad)
            delta_y = distancia_cm * math.sin(angulo_rad) if direcao == 'frente' else -distancia_cm * math.sin(angulo_rad)

            self.posicao_atual['x'] += delta_x
            self.posicao_atual['y'] += delta_y

            print(f"Posição atualizada: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}")
            return True
        except Exception as e:
            print(f"❌ Erro no movimento em linha reta: {e}")
            self.parar()
            return False

    def parar(self):
        """Parar todos os movimentos"""
        try:
            self.mpu.enviar_comando('parar')
            self.movimento_ativo = False
            print("🛑 Movimento parado")
            return True
        except Exception as e:
            print(f"❌ Erro ao parar: {e}")
            return False

    def virar_90_graus(self, direcao='direita'):
        """Fazer curva de 90 graus baseada em ângulo do MPU6050 com precisão melhorada"""
        try:
            print(f"🔄 Virando 90° para a {direcao}")

            # Obter ângulo inicial
            angulo_inicial = self.get_current_angle()
            if angulo_inicial is None:
                print("❌ Não foi possível obter ângulo inicial")
                return False

            # Determinar direção da curva
            # NOTA: Sentido invertido devido à orientação do MPU6050
            sentido = -1 if direcao == 'direita' else 1  # Invertido

            # Ângulo alvo
            angulo_alvo = angulo_inicial + (self.angulo_curva * sentido)

            # Normalizar ângulo alvo (0-360)
            angulo_alvo = angulo_alvo % 360

            # Compensação de inércia: parar alguns graus antes do alvo
            compensacao_inercia = 2.0  # graus para compensar inércia
            angulo_parada = angulo_alvo - (compensacao_inercia * sentido)
            angulo_parada = angulo_parada % 360

            print(f"Ângulo inicial: {angulo_inicial:.1f}°")
            print(f"Ângulo alvo: {angulo_alvo:.1f}°")
            print(f"Ângulo de parada: {angulo_parada:.1f}° (compensação: {compensacao_inercia:.1f}°)")

            # Iniciar movimento de rotação com velocidade ainda mais reduzida para precisão
            # NOTA: Comandos invertidos devido à orientação do MPU6050
            comando = 'virar_esquerda' if direcao == 'direita' else 'virar_direita'  # Invertido
            self.mpu.enviar_comando(comando, {'velocidade': 25})  # Velocidade ainda mais reduzida

            # Aguardar alcance do ângulo de parada
            timeout = 25  # segundos máximo aumentado
            inicio = time.time()
            leituras_consecutivas_no_alvo = 0
            leituras_necessarias = 1  # Reduzido para parar mais rápido
            leituras_consecutivas_falha = 0
            max_falhas_consecutivas = 15  # Aumentado devido ao polling mais lento
            slowed_down = False

            while time.time() - inicio < timeout:
                angulo_atual = self.get_current_angle()
                if angulo_atual is None:
                    leituras_consecutivas_falha += 1
                    print(f"  ⚠️ Falha ao obter ângulo ({leituras_consecutivas_falha}/{max_falhas_consecutivas})")
                    if leituras_consecutivas_falha >= max_falhas_consecutivas:
                        print("❌ Muitas falhas consecutivas, parando movimento")
                        break
                    continue
                else:
                    leituras_consecutivas_falha = 0

                # Calcular diferença angular até o ponto de parada
                diff = self.calcular_diferenca_angular(angulo_atual, angulo_parada)

                print(f"Ângulo atual: {angulo_atual:.1f}°, Diferença para parada: {diff:.1f}°")

                # Reduzir velocidade quando se aproximando do ponto de parada
                if abs(diff) < 10 and not slowed_down:
                    print("  🐌 Reduzindo velocidade ...")
                    self.mpu.enviar_comando(comando, {'velocidade': 10})  # Velocidade ainda mais reduzida
                    slowed_down = True

                # Verificar se chegou no ponto de parada
                if abs(diff) <= 0.45:  # Tolerância menor para o ponto de parada
                    leituras_consecutivas_no_alvo += 1
                    print(f"  ✅ Leitura {leituras_consecutivas_no_alvo}/{leituras_necessarias} no ponto de parada")
                    if leituras_consecutivas_no_alvo >= leituras_necessarias:
                        print("✅ Ponto de parada alcançado!")
                        break
                else:
                    leituras_consecutivas_no_alvo = 0

                time.sleep(0.1)  # Leitura menos frequente para evitar sobrecarga serial

            # Parar movimento imediatamente
            self.parar()

            # Aguardar estabilização e obter ângulo final
            time.sleep(0.5)  # Mais tempo para estabilização
            angulo_final = self.get_current_angle()
            if angulo_final is not None:
                self.posicao_atual['angulo'] = angulo_final
                diff_final = self.calcular_diferenca_angular(angulo_final, angulo_alvo)
                print(f"Ângulo final: {angulo_final:.1f}°, Diferença do alvo: {diff_final:.1f}°")

            return True

        except Exception as e:
            print(f"❌ Erro na curva de 90°: {e}")
            self.parar()
            return False

    def get_current_angle(self):
        """Obter o ângulo atual (yaw) do MPU6050 com retry"""
        for tentativa in range(3):
            status = self.mpu.obter_status_completo()
            if status and status.get('orientacao'):
                return status['orientacao']['yaw']
            print(f"  ⚠️ Tentativa {tentativa+1} falhou, tentando novamente...")
            time.sleep(0.05)  # Pequeno delay entre tentativas
        print("  ❌ Todas as tentativas falharam")
        return None

    def calcular_diferenca_angular(self, angulo_atual, angulo_alvo):
        """Calcular a menor diferença angular considerando wrap-around 0-360°"""
        diff = angulo_alvo - angulo_atual

        # Normalizar para -180 a +180
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        return diff

    def executar_rota_quadrada(self, lado_cm=100):
        """Executar rota quadrada (teste de navegação)"""
        try:
            print("🔲 EXECUTANDO ROTA QUADRADA")
            print("=" * 30)
            print(f"📏 Lado: {lado_cm}cm")

            rota = [
                ('frente', lado_cm),
                ('direita', 90),
                ('frente', lado_cm),
                ('direita', 90),
                ('frente', lado_cm),
                ('direita', 90),
                ('frente', lado_cm),
                ('direita', 90)
            ]

            for i, (tipo, valor) in enumerate(rota, 1):
                print(f"\n📍 Passo {i}/8: {tipo} {valor}")
                print(f"📍 Posição atual: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}, Ângulo={self.posicao_atual['angulo']:.1f}°")

                if tipo == 'frente':
                    if not self.mover_em_linha_reta(valor, 'frente'):
                        print("❌ Falha no movimento em linha reta")
                        return False
                elif tipo in ['direita', 'esquerda']:
                    if not self.virar_90_graus(tipo):
                        print("❌ Falha na curva")
                        return False

                time.sleep(1)  # Pausa entre movimentos

            print("✅ ROTA QUADRADA CONCLUÍDA!")
            print(f"Posição final: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}")
            return True
        except Exception as e:
            print(f"❌ Erro na rota quadrada: {e}")
            self.parar()
            return False

    def executar_rota_personalizada(self, comandos):
        """Executar rota personalizada"""
        print("🚀 EXECUTANDO ROTA PERSONALIZADA")
        print("=" * 35)

        for i, comando in enumerate(comandos, 1):
            print(f"\n📍 Comando {i}: {comando}")

            if comando['tipo'] == 'mover':
                if not self.mover_em_linha_reta(comando['distancia'], comando.get('direcao', 'frente')):
                    print("❌ Falha no movimento")
                    return False

            elif comando['tipo'] == 'virar':
                if not self.virar_90_graus(comando.get('direcao', 'direita')):
                    print("❌ Falha na curva")
                    return False

            time.sleep(1)

        print("✅ ROTA PERSONALIZADA CONCLUÍDA!")
        return True

    def mostrar_status(self):
        """Mostrar status atual"""
        status = self.mpu.obter_status_completo()

        print("\n📊 STATUS DO AGV")
        print("=" * 20)
        print(f"Posição: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}, Ângulo={self.posicao_atual['angulo']:.1f}°")
        print(f"🔋 Conectado: {'Sim' if status else 'Não'}")
        print(f"📏 Distância: {self.distancia_minima}cm (simulado)")

        if status and status['orientacao']:
            print(f"Yaw: {status['orientacao']['yaw']:.1f}°")
            print(f"Pitch: {status['orientacao']['pitch']:.1f}°")
            print(f"Roll: {status['orientacao']['roll']:.1f}°")
        print(f"🔄 Movimento: {'Sim' if status and status.get('movimento_detectado', False) else 'Não'}")

def main():
    """Função principal"""
    print("🎯 NAVEGAÇÃO BÁSICA AGV")
    print("=" * 25)

    # Configurações
    port = get_esp32_port()  # Porta do config.py

    # Criar navegação
    nav = BasicNavigation(esp32_port=port)

    # Inicializar
    if not nav.inicializar():
        return

    # Menu de opções
    while True:
        print("\n" + "="*40)
        print("🎮 MENU DE NAVEGAÇÃO")
        print("="*40)
        print("1. Teste em linha reta (50cm)")
        print("2. Teste de curva 90° (direita)")
        print("3. Teste de curva 90° (esquerda)")
        print("4. Executar rota quadrada")
        print("5. Mostrar status")
        print("6. Parar motores")
        print("0. Sair")
        print("="*40)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                nav.mover_em_linha_reta(50, 'frente')
            elif opcao == '2':
                nav.virar_90_graus('direita')
            elif opcao == '3':
                nav.virar_90_graus('esquerda')
            elif opcao == '4':
                nav.executar_rota_quadrada(50)
            elif opcao == '5':
                nav.mostrar_status()
            elif opcao == '6':
                nav.parar()
                print("🛑 Motores parados")
            elif opcao == '0':
                nav.parar()
                print("👋 Saindo...")
                break
            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            nav.parar()
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            nav.parar()

if __name__ == "__main__":
    main()