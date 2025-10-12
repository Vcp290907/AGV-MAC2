#!/usr/bin/env python3
"""
Controle de Missões do AGV - Sistema Completo de Navegação
Coordena navegação, detecção de QR codes e execução de pedidos
"""

import time
import json
import requests
from datetime import datetime
from navigation_basic import BasicNavigation
# from qr_reader_with_api import QRReaderWithAPI  # Desabilitado - usa picamera2
from qr_reader_opencv_only import OpenCVOnlyQRReader
from config import get_esp32_port

class AGVMissionControl:
    """Sistema completo de controle de missões do AGV"""

    def __init__(self, pc_ip="192.168.0.100", pc_port=5000, esp32_port=None):
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.base_url = f"http://{pc_ip}:{pc_port}"
        
        # Usar porta do config se não especificada
        esp32_port = esp32_port or get_esp32_port()
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.base_url = f"http://{pc_ip}:{pc_port}"

        # Componentes do sistema
        self.navigation = BasicNavigation(esp32_port=esp32_port)
        # self.qr_reader = QRReaderWithAPI(pc_ip=pc_ip, pc_port=pc_port)  # Desabilitado
        self.qr_detector = OpenCVOnlyQRReader()  # Detector direto para navegação

        # Estado da missão
        self.missao_ativa = None
        self.itens_coletados = []
        self.posicao_atual = {'x': 0, 'y': 0, 'angulo': 0}

        # Configurações
        self.distancia_ate_prateleira = 30  # cm até a prateleira após curva
        self.tempo_busca_item = 5  # segundos para "pegar" item

    def inicializar_sistema(self):
        """Inicializar todos os componentes"""
        print("INICIALIZANDO SISTEMA AGV MISSION CONTROL")
        print("=" * 50)

        # Inicializar navegação
        if not self.navigation.inicializar():
            print("❌ Falha na inicialização da navegação")
            return False

        # Inicializar detector QR
        if not self.qr_detector.initialize():
            print("❌ Falha na inicialização do detector QR")
            return False

        # Testar conexão com PC (opcional)
        try:
            import requests
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                print("✅ Conexão com PC estabelecida!")
            else:
                print("⚠️ PC não respondeu corretamente, mas continuando...")
        except:
            print("⚠️ Não foi possível conectar ao PC, mas continuando...")

        print("✅ Sistema AGV inicializado com sucesso!")
        return True

    def obter_pedido_ativo(self):
        """Obter pedido ativo do PC"""
        try:
            response = requests.get(f"{self.base_url}/pedidos/ativo", timeout=5)
            if response.status_code == 200:
                pedido = response.json()
                if pedido:
                    return pedido
            return None
        except Exception as e:
            print(f"❌ Erro ao obter pedido ativo: {e}")
            return None

    def iniciar_missao(self, pedido):
        """Iniciar missão baseada no pedido"""
        print(f"🎯 INICIANDO MISSÃO: Pedido #{pedido['id']}")
        print("=" * 40)

        self.missao_ativa = {
            'pedido': pedido,
            'itens_por_subcorredor': self._organizar_itens_por_subcorredor(pedido),
            'status': 'iniciada',
            'inicio': datetime.now()
        }

        # Organizar rota baseada nos subcorredores
        rota = self._calcular_rota_otimizada()
        self.missao_ativa['rota'] = rota

        print(f"📋 Itens a coletar: {len(self.missao_ativa['itens_por_subcorredor'])} subcorredores")
        print(f"🛣️ Rota calculada: {len(rota)} paradas")

        return True

    def _organizar_itens_por_subcorredor(self, pedido):
        """Organizar itens por subcorredor"""
        itens_por_subcorredor = {}

        # Itens do pedido
        if 'itens' in pedido and pedido['itens']:
            itens_lista = pedido['itens'].split(',')
            corredores = pedido.get('corredores', '').split(',') if pedido.get('corredores') else []
            subcorredores = pedido.get('sub_corredores', '').split(',') if pedido.get('sub_corredores') else []

            for i, item_nome in enumerate(itens_lista):
                corredor = corredores[i] if i < len(corredores) else '1'
                subcorredor = subcorredores[i] if i < len(subcorredores) else '1'

                chave = f"{corredor}_{subcorredor}"

                if chave not in itens_por_subcorredor:
                    itens_por_subcorredor[chave] = []

                itens_por_subcorredor[chave].append({
                    'nome': item_nome.strip(),
                    'corredor': corredor,
                    'subcorredor': subcorredor
                })

        return itens_por_subcorredor

    def _calcular_rota_otimizada(self):
        """Calcular rota otimizada baseada nos subcorredores"""
        rota = []

        # Ordenar subcorredores por proximidade (simplificado)
        subcorredores = sorted(self.missao_ativa['itens_por_subcorredor'].keys())

        for subcorredor in subcorredores:
            rota.append({
                'tipo': 'navegacao',
                'destino': subcorredor,
                'acao': 'coletar_itens'
            })

        # Adicionar ponto de entrega
        rota.append({
            'tipo': 'entrega',
            'destino': 'Entrega',
            'acao': 'finalizar'
        })

        return rota

    def executar_missao(self):
        """Executar missão completa"""
        if not self.missao_ativa:
            print("❌ Nenhuma missão ativa")
            return False

        print("🚀 EXECUTANDO MISSÃO COMPLETA")
        print("=" * 35)

        try:
            for i, etapa in enumerate(self.missao_ativa['rota'], 1):
                print(f"\n📍 Etapa {i}/{len(self.missao_ativa['rota'])}: {etapa['tipo']} - {etapa['destino']}")

                if etapa['tipo'] == 'navegacao':
                    if not self._navegar_ate_subcorredor(etapa['destino']):
                        print("❌ Falha na navegação")
                        return False

                    if not self._coletar_itens_subcorredor(etapa['destino']):
                        print("❌ Falha na coleta")
                        return False

                elif etapa['tipo'] == 'entrega':
                    if not self._ir_ate_entrega():
                        print("❌ Falha ao ir para entrega")
                        return False

            # Missão concluída
            self._finalizar_missao()
            return True

        except Exception as e:
            print(f"❌ Erro durante missão: {e}")
            self.navigation.parar()
            return False

    def _navegar_ate_subcorredor(self, subcorredor_destino):
        """Navegar até o QR code do subcorredor usando câmera e QR detection"""
        print(f"🧭 Navegando até subcorredor: {subcorredor_destino}")

        # QR code esperado baseado no subcorredor
        qr_esperado = f"Corredor01_{subcorredor_destino}"
        print(f"🔍 Procurando QR code: {qr_esperado}")

        # Usar câmera para detectar QR code enquanto navega
        qr_detectado = None
        tentativas = 0
        max_tentativas = 10

        while qr_detectado != qr_esperado and tentativas < max_tentativas:
            # Mover um pouco para frente
            if not self.navigation.mover_em_linha_reta(20, 'frente'):  # 20cm por vez
                print("❌ Falha no movimento durante busca")
                return False

            # Verificar QR code com câmera
            try:
                qr_resultado = self.qr_reader.detectar_qr_code()
                if qr_resultado and qr_resultado['detectado']:
                    qr_detectado = qr_resultado['codigo']
                    print(f"📷 QR code detectado: {qr_detectado}")

                    if qr_detectado == qr_esperado:
                        print("✅ QR code correto encontrado!")
                        break
                    else:
                        print(f"⚠️ QR code errado detectado: {qr_detectado} (esperado: {qr_esperado})")
                        # Continuar procurando
                else:
                    print("📷 Nenhum QR code detectado, continuando...")

            except Exception as e:
                print(f"⚠️ Erro na detecção de QR: {e}")

            tentativas += 1

        if qr_detectado != qr_esperado:
            print(f"❌ QR code {qr_esperado} não encontrado após {max_tentativas} tentativas")
            return False

        # QR encontrado! Fazer curva de 90° para acessar prateleira
        print("🔄 Fazendo curva de 90° para acessar prateleira")
        if not self.navigation.virar_90_graus('direita'):
            return False

        # Mover até a prateleira
        print(f"📏 Movendo {self.distancia_ate_prateleira}cm até a prateleira")
        if not self.navigation.mover_em_linha_reta(self.distancia_ate_prateleira, 'frente'):
            return False

        return True

    def _coletar_itens_subcorredor(self, subcorredor):
        """Coletar todos os itens do subcorredor usando QR codes"""
        print(f"🤖 Iniciando coleta no subcorredor: {subcorredor}")

        itens_subcorredor = self.missao_ativa['itens_por_subcorredor'].get(subcorredor, [])

        for item in itens_subcorredor:
            print(f"📦 Procurando item: {item['nome']}")

            # Usar câmera superior para detectar QR do item
            qr_item_esperado = f"TAG{item['nome'].replace(' ', '')[:4].upper()}"
            print(f"🔍 Procurando QR code do item: {qr_item_esperado}")

            qr_detectado = None
            tentativas_item = 0
            max_tentativas_item = 5

            while qr_detectado != qr_item_esperado and tentativas_item < max_tentativas_item:
                try:
                    qr_resultado = self.qr_detector.detectar_qr_code()
                    if qr_resultado and qr_resultado['detectado']:
                        qr_detectado = qr_resultado['codigo']
                        print(f"📷 QR code detectado: {qr_detectado}")

                        if qr_detectado == qr_item_esperado:
                            print("✅ Item encontrado!")
                            break
                        else:
                            print(f"⚠️ QR code errado: {qr_detectado} (esperado: {qr_item_esperado})")
                    else:
                        print("📷 Nenhum QR code detectado, ajustando posição...")

                        # Pequeno movimento para procurar melhor
                        if not self.navigation.mover_em_linha_reta(5, 'frente'):
                            break

                except Exception as e:
                    print(f"⚠️ Erro na detecção: {e}")

                tentativas_item += 1
                time.sleep(0.5)

            if qr_detectado != qr_item_esperado:
                print(f"❌ Item {item['nome']} não encontrado após {max_tentativas_item} tentativas")
                continue  # Pular para próximo item

            # Item encontrado! Simular coleta
            print(f"🤲 Coletando item: {item['nome']}")
            print("⏳ Aguardando remoção manual do item...")
            time.sleep(self.tempo_busca_item)

            # Registrar coleta
            self.itens_coletados.append({
                'item': item,
                'timestamp': datetime.now(),
                'subcorredor': subcorredor
            })

            print(f"✅ Item coletado: {item['nome']}")

        # Dar ré e voltar à linha principal
        print("⬅️ Dando ré para voltar à linha principal")
        if not self.navigation.mover_em_linha_reta(self.distancia_ate_prateleira, 'tras'):
            return False

        # Virar -90° para voltar à linha
        print("🔄 Virando -90° para voltar à linha principal")
        if not self.navigation.virar_90_graus('esquerda'):
            return False

        return True

    def _ir_ate_entrega(self):
        """Ir até o ponto de entrega usando QR code"""
        print("📦 Indo para ponto de entrega")

        # QR code esperado para entrega
        qr_entrega = "Entrega"
        print(f"🔍 Procurando QR code: {qr_entrega}")

        # Navegar procurando QR code de entrega
        qr_detectado = None
        tentativas = 0
        max_tentativas = 15

        while qr_detectado != qr_entrega and tentativas < max_tentativas:
            # Mover um pouco para frente
            if not self.navigation.mover_em_linha_reta(30, 'frente'):  # 30cm por vez
                print("❌ Falha no movimento durante busca de entrega")
                return False

            # Verificar QR code com câmera
            try:
                qr_resultado = self.qr_detector.detectar_qr_code()
                if qr_resultado and qr_resultado['detectado']:
                    qr_detectado = qr_resultado['codigo']
                    print(f"📷 QR code detectado: {qr_detectado}")

                    if qr_detectado == qr_entrega:
                        print("✅ Ponto de entrega encontrado!")
                        break
                    else:
                        print(f"⚠️ QR code errado: {qr_detectado} (esperado: {qr_entrega})")
                else:
                    print("📷 Nenhum QR code detectado, continuando...")

            except Exception as e:
                print(f"⚠️ Erro na detecção de QR: {e}")

            tentativas += 1

        if qr_detectado != qr_entrega:
            print(f"❌ Ponto de entrega não encontrado após {max_tentativas} tentativas")
            return False

        # Chegou ao ponto de entrega!
        self._notificar_entrega()
        return True

    def _notificar_entrega(self):
        """Notificar chegada ao ponto de entrega"""
        print("\n" + "="*50)
        print("🎉 CHEGADA AO PONTO DE ENTREGA!")
        print("="*50)
        print("📦 Itens coletados:")

        for i, item in enumerate(self.itens_coletados, 1):
            print(f"   {i}. {item['item']['nome']} (Subcorredor {item['subcorredor']})")

        print(f"\n📊 Total de itens: {len(self.itens_coletados)}")
        print("⏰ Aguardando retirada dos itens...")
        # Aqui poderia enviar notificação para o PC/dashboard

    def _finalizar_missao(self):
        """Finalizar missão"""
        print("\n" + "="*50)
        print("✅ MISSÃO CONCLUÍDA COM SUCESSO!")
        print("="*50)

        self.missao_ativa['status'] = 'concluida'
        self.missao_ativa['fim'] = datetime.now()

        # Calcular duração
        duracao = self.missao_ativa['fim'] - self.missao_ativa['inicio']
        print(f"⏱️ Duração: {duracao}")

        # Resetar estado
        self.missao_ativa = None

    def executar_teste(self):
        """Executar teste do sistema"""
        print("🧪 EXECUTANDO TESTE DO SISTEMA AGV")
        print("=" * 40)

        # Teste básico de navegação
        print("1. Teste de movimento em linha reta...")
        if not self.navigation.mover_em_linha_reta(30, 'frente'):
            return False

        print("2. Teste de curva 90°...")
        if not self.navigation.virar_90_graus('direita'):
            return False

        print("3. Teste de movimento de retorno...")
        if not self.navigation.mover_em_linha_reta(30, 'tras'):
            return False

        print("4. Teste de curva -90°...")
        if not self.navigation.virar_90_graus('esquerda'):
            return False

        print("✅ Todos os testes passaram!")
        return True

def main():
    """Função principal"""
    print("AGV MISSION CONTROL")
    print("=" * 25)

    # Configurações
    pc_ip = "192.168.0.100"
    pc_port = 5000
    esp32_port = get_esp32_port()

    # Criar controle de missões
    agv = AGVMissionControl(pc_ip=pc_ip, pc_port=pc_port, esp32_port=esp32_port)

    # Inicializar sistema
    if not agv.inicializar_sistema():
        return

    # Menu principal
    while True:
        print("\n" + "="*50)
        print("🎮 CONTROLE DE MISSÕES AGV")
        print("="*50)
        print("1. Verificar pedidos ativos")
        print("2. Executar missão ativa")
        print("3. Executar teste do sistema")
        print("4. Mostrar status")
        print("5. Parar motores")
        print("0. Sair")
        print("="*50)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                pedido = agv.obter_pedido_ativo()
                if pedido:
                    print(f"📋 Pedido ativo encontrado: #{pedido['id']}")
                    print(f"👤 Usuário: {pedido['usuario_nome']}")
                    print(f"📦 Itens: {pedido['itens']}")
                    agv.iniciar_missao(pedido)
                else:
                    print("❌ Nenhum pedido ativo encontrado")

            elif opcao == '2':
                if agv.missao_ativa:
                    agv.executar_missao()
                else:
                    print("❌ Nenhuma missão ativa. Verifique pedidos primeiro.")

            elif opcao == '3':
                agv.executar_teste()

            elif opcao == '4':
                agv.navigation.mostrar_status()

            elif opcao == '5':
                agv.navigation.parar()
                print("🛑 Motores parados")

            elif opcao == '0':
                agv.navigation.parar()
                print("👋 Saindo...")
                break

            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            agv.navigation.parar()
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            agv.navigation.parar()

if __name__ == "__main__":
    main()