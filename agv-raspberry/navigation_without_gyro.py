#!/usr/bin/env python3
"""
Navegação Básica SEM Giroscópio
Movimento em linha reta + curvas de 90 graus usando apenas temporização
"""

import time
import math
from datetime import datetime

class BasicNavigationWithoutGyro:
    """Navegação básica sem giroscópio - usa apenas temporização"""

    def __init__(self, esp32_port='/dev/ttyUSB0'):
        # Simular conexão ESP32 (sem giroscópio real)
        self.esp32_port = esp32_port
        self.velocidade_base = 80  # Velocidade padrão (0-100)

        # Configurações de navegação (baseadas em testes)
        self.angulo_curva = 90  # Graus para curvas
        self.tempo_curva_90_graus = 2.5  # segundos para fazer 90° (ajuste baseado em testes)
        self.distancia_minima = 50  # cm (simulado)

        # Estado atual
        self.posicao_atual = {'x': 0, 'y': 0, 'angulo': 0}
        self.movimento_ativo = False

        # Simular ESP32
        self.esp32_simulado = True

    def inicializar(self):
        """Inicializar navegação sem giroscópio"""
        print("🚀 INICIALIZANDO NAVEGAÇÃO BÁSICA (SEM GIROSCÓPIO)")
        print("=" * 55)
        print("⚠️  Usando temporização para curvas - sem sensor de orientação")
        print("💡 Para melhor precisão, considere adicionar MPU6050")

        # Simular inicialização do ESP32
        print(f"📡 Conectando ao ESP32 simulado: {self.esp32_port}")
        time.sleep(1)
        print("✅ ESP32 simulado inicializado!")

        print("✅ Navegação sem giroscópio inicializada!")
        return True

    def mover_em_linha_reta(self, distancia_cm, direcao='frente'):
        """Mover em linha reta por uma distância usando temporização"""
        print(f"📏 Movendo em linha reta: {distancia_cm}cm para {direcao}")

        # Calcular tempo baseado na velocidade (ajuste baseado em testes reais)
        # Velocidade aproximada: 25 cm/s (ajuste conforme testes)
        velocidade_cm_por_segundo = 25
        tempo_movimento = distancia_cm / velocidade_cm_por_segundo

        print(".1f"
        # Simular comando de movimento
        comando = 'mover_frente' if direcao == 'frente' else 'mover_tras'
        print(f"📡 Enviando comando: {comando} (velocidade: {self.velocidade_base})")

        # Simular movimento
        inicio = time.time()
        while time.time() - inicio < tempo_movimento:
            progresso = (time.time() - inicio) / tempo_movimento * 100
            print(".1f"            time.sleep(0.5)

        # Simular parada
        print("📡 Enviando comando: parar")
        time.sleep(0.5)

        # Atualizar posição (simulação)
        angulo_rad = math.radians(self.posicao_atual['angulo'])
        delta_x = distancia_cm * math.cos(angulo_rad) if direcao == 'frente' else -distancia_cm * math.cos(angulo_rad)
        delta_y = distancia_cm * math.sin(angulo_rad) if direcao == 'frente' else -distancia_cm * math.sin(angulo_rad)

        self.posicao_atual['x'] += delta_x
        self.posicao_atual['y'] += delta_y

        print(".1f"        return True

    def virar_90_graus(self, direcao='direita'):
        """Fazer curva de 90 graus usando temporização"""
        print(f"🔄 Virando 90° para a {direcao} (usando temporização)")

        print(".1f"
        # Comando de movimento de rotação
        comando = 'virar_direita' if direcao == 'direita' else 'virar_esquerda'
        print(f"📡 Enviando comando: {comando} (velocidade: 60)")

        # Aguardar tempo necessário para 90°
        tempo_restante = self.tempo_curva_90_graus
        while tempo_restante > 0:
            print(".1f"            time.sleep(0.5)
            tempo_restante -= 0.5

        # Simular parada
        print("📡 Enviando comando: parar")
        time.sleep(0.5)

        # Atualizar ângulo da posição
        sentido = 1 if direcao == 'direita' else -1
        self.posicao_atual['angulo'] = (self.posicao_atual['angulo'] + (self.angulo_curva * sentido)) % 360

        print(".1f"        return True

    def parar(self):
        """Parar movimento"""
        print("📡 Enviando comando: parar")
        self.movimento_ativo = False
        time.sleep(0.5)  # Aguardar parada completa

    def executar_rota_quadrada(self, lado_cm=100):
        """Executar rota quadrada (teste de navegação)"""
        print("🔲 EXECUTANDO ROTA QUADRADA (SEM GIROSCÓPIO)")
        print("=" * 45)
        print(f"📏 Lado: {lado_cm}cm")
        print("⚠️  Curvas usam temporização - podem não ser precisas")

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
        print(".1f"        return True

    def calibrar_tempo_curva(self):
        """Calibrar tempo necessário para curvas de 90°"""
        print("🔧 CALIBRAÇÃO DO TEMPO DE CURVA")
        print("=" * 35)
        print("Isso ajudará a ajustar a precisão das curvas")

        tempos_teste = [2.0, 2.5, 3.0, 3.5]

        for tempo in tempos_teste:
            print(f"\n🧪 Testando tempo: {tempo}s")
            resposta = input("Fazer teste? (s/n): ").strip().lower()

            if resposta == 's':
                print(f"📡 Testando curva com {tempo}s...")

                # Simular curva
                self.tempo_curva_90_graus = tempo
                if self.virar_90_graus('direita'):
                    print("✅ Teste concluído")

                    qualidade = input("Qualidade da curva (1-5, 5=perfeita): ").strip()
                    try:
                        nota = int(qualidade)
                        if nota >= 4:
                            print(f"🎯 Tempo {tempo}s parece bom!")
                            return True
                    except:
                        pass

        print("💡 Use o tempo que deu melhor resultado")
        return False

    def mostrar_status(self):
        """Mostrar status atual"""
        print("\n📊 STATUS DO AGV (SEM GIROSCÓPIO)")
        print("=" * 35)
        print(".1f"        print(".1f"        print(".1f"        print(f"⚠️  Sem sensor de orientação (giroscópio)")
        print(f"⏱️  Tempo para curva 90°: {self.tempo_curva_90_graus}s")
        print(f"📡 ESP32: {'Simulado' if self.esp32_simulado else 'Real'}")

def main():
    """Função principal"""
    print("🎯 NAVEGAÇÃO BÁSICA SEM GIROSCÓPIO")
    print("=" * 40)

    # Configurações
    port = '/dev/ttyUSB0'  # Mesmo que com giroscópio

    # Criar navegação sem giroscópio
    nav = BasicNavigationWithoutGyro(esp32_port=port)

    # Inicializar
    if not nav.inicializar():
        return

    # Menu de opções
    while True:
        print("\n" + "="*50)
        print("🎮 NAVEGAÇÃO SEM GIROSCÓPIO")
        print("="*50)
        print("1. Teste em linha reta (50cm)")
        print("2. Teste de curva 90° (direita)")
        print("3. Teste de curva 90° (esquerda)")
        print("4. Executar rota quadrada")
        print("5. Calibrar tempo de curva")
        print("6. Mostrar status")
        print("7. Parar motores")
        print("0. Sair")
        print("="*50)

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
                nav.calibrar_tempo_curva()
            elif opcao == '6':
                nav.mostrar_status()
            elif opcao == '7':
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