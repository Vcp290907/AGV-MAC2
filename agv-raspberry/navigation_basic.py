#!/usr/bin/env python3
"""
Navegação Básica do AGV
Movimento em linha reta + curvas de 90 graus usando MPU6050
"""

import time
import math
from datetime import datetime
from mpu6050_integration import MPU6050Integration
from config import get_esp32_port

class BasicNavigation:
    """Navegação básica: linha reta + curvas de 90°"""

    def __init__(self, esp32_port=None):
        self.mpu = MPU6050Integration(esp32_port=esp32_port or get_esp32_port())
        self.mpu = MPU6050Integration(esp32_port=esp32_port)
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
                # Verificar se houve movimento excessivo (queda)
                if status['queda_detectada']:
                    print("⚠️ POSSÍVEL QUEDA DETECTADA - PARANDO!")
                    self.parar()
                    return False

                # Mostrar progresso
                progresso = (time.time() - inicio) / tempo_movimento * 100
                print(".1f"
            time.sleep(0.1)

        # Parar movimento
        self.parar()

        # Atualizar posição (simulação)
        angulo_rad = math.radians(self.posicao_atual['angulo'])
        delta_x = distancia_cm * math.cos(angulo_rad) if direcao == 'frente' else -distancia_cm * math.cos(angulo_rad)
        delta_y = distancia_cm * math.sin(angulo_rad) if direcao == 'frente' else -distancia_cm * math.sin(angulo_rad)

        self.posicao_atual['x'] += delta_x
        self.posicao_atual['y'] += delta_y

        print(".1f"        return True

    def virar_90_graus(self, direcao='direita'):
        """Fazer curva de 90 graus usando giroscópio"""
        print(f"🔄 Virando 90° para a {direcao}")

        # Determinar direção da curva
        sentido = 1 if direcao == 'direita' else -1

        # Angulo alvo
        angulo_inicial = self.posicao_atual['angulo']
        angulo_alvo = angulo_inicial + (self.angulo_curva * sentido)

        # Normalizar ângulo (0-360)
        angulo_alvo = angulo_alvo % 360

        print(".1f"
        # Iniciar movimento de rotação
        comando = 'virar_direita' if direcao == 'direita' else 'virar_esquerda'
        self.mpu.enviar_comando(comando, {'velocidade': 60})  # Velocidade menor para curvas

        # Monitorar rotação usando giroscópio
        tempo_maximo = 10  # segundos
        inicio = time.time()

        while time.time() - inicio < tempo_maximo:
            status = self.mpu.obter_status_completo()

            if status and status['orientacao']:
                angulo_atual = status['orientacao']['yaw']

                # Calcular diferença angular
                diff = abs(angulo_atual - angulo_alvo)
                diff = min(diff, 360 - diff)  # Considerar menor ângulo

                print(".1f"
                # Verificar se chegou no ângulo desejado
                if diff <= self.tolerancia_angulo:
                    print("✅ Ângulo alcançado!")
                    break

                # Verificar se houve movimento excessivo (queda)
                if status['queda_detectada']:
                    print("⚠️ POSSÍVEL QUEDA DETECTADA - PARANDO!")
                    self.parar()
                    return False

            time.sleep(0.1)

        # Parar movimento
        self.parar()

        # Atualizar ângulo da posição
        self.posicao_atual['angulo'] = angulo_alvo

        print(".1f"        return True

    def parar(self):
        """Parar movimento"""
        self.mpu.enviar_comando('parar')
        self.movimento_ativo = False
        time.sleep(0.5)  # Aguardar parada completa

    def executar_rota_quadrada(self, lado_cm=100):
        """Executar rota quadrada (teste de navegação)"""
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
        print(".1f"        return True

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
        print(".1f"        print(".1f"        print(".1f"
        if status and status['orientacao']:
            print(".1f"            print(".1f"            print(".1f"
        print(f"🔄 Movimento: {'Sim' if status and status.get('movimento_detectado', False) else 'Não'}")
        print(f"📉 Queda: {'Sim' if status and status.get('queda_detectada', False) else 'Não'}")

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