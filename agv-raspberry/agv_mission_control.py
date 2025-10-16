#!/usr/bin/env python3
"""
Controle de Missões do AGV - Sistema Completo de Navegação
Coordena navegação, detecção de QR codes e execução de pedidos
"""

import os
import sys

# Configurar PYTHONPATH para acessar bibliotecas do sistema (necessário para Picamera2)
system_python_path = '/usr/lib/python3/dist-packages'
if system_python_path not in sys.path:
    sys.path.insert(0, system_python_path)

import time
import threading
import json
import requests
from datetime import datetime
from navigation_basic import BasicNavigation
from line_following_navigation import LineFollowingNavigation
from qr_reader_opencv_only import OpenCVOnlyQRReader
from config_manager import get_config, get_backend_url

class AGVMissionControl:
    """Sistema completo de controle de missões do AGV"""

    def __init__(self, pc_ip=None, pc_port=None, esp32_port=None):
        # Usar configurações do config.json se não especificadas
        self.pc_ip = pc_ip or get_config('backend.ip', '192.168.0.120')
        self.pc_port = pc_port or get_config('backend.port', 5000)
        self.base_url = get_backend_url()

        # Usar porta do config se não especificada
        esp32_port = esp32_port or get_config('esp32.port', '/dev/ttyACM0')
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.base_url = f"http://{self.pc_ip}:{self.pc_port}"

        # Componentes do sistema
        self.navigation = BasicNavigation(esp32_port=esp32_port)
        self.line_navigation = LineFollowingNavigation(esp32_port=esp32_port)
        # self.qr_reader = QRReaderWithAPI(pc_ip=pc_ip, pc_port=pc_port)  # Desabilitado
        self.qr_detector = OpenCVOnlyQRReader()  # Detector direto para navegação

        # Estado da missão
        self.missao_ativa = None
        self.itens_coletados = []
        self.posicao_atual = {'x': 0, 'y': 0, 'angulo': 0}

        # Configurações
        self.tempo_busca_item = 5  # segundos para "pegar" item
        self.agv_id = get_config('agv.id', 'agv_1')
        # Controle do loop de missões
        self._mission_loop_stop = threading.Event()
        self._mission_loop_thread = None

    def inicializar_sistema(self):
        """Inicializar todos os componentes"""
        print("INICIALIZANDO SISTEMA AGV MISSION CONTROL")
        print("=" * 50)

        # Inicializar navegação básica
        if not self.navigation.inicializar():
            print("Falha na inicializacao da navegacao basica")
            return False

        # Inicializar navegação por linha
        if not self.line_navigation.initialize():
            print("❌ Falha na inicialização da navegação por linha")
            return False

        # Inicializar detector QR (opcional - continua se falhar)
        if not self.qr_detector.initialize():
            print("Aviso: Camera nao disponivel - sistema funcionara sem QR detection")
            print("Para usar camera: sudo apt-get install v4l-utils")
            # Não retorna False - permite que o sistema continue sem câmera

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

    def obter_proximo_comando(self):
        """Consulta o backend por /agv/next_command e retorna a missão (se houver)."""
        try:
            url = f"{self.base_url}/agv/next_command"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get('success') and data.get('command'):
                    return data['command']
            return None
        except Exception as e:
            print(f"❌ Erro ao obter próximo comando: {e}")
            return None

    def reportar_status(self, estado, detalhe=None, qr=None, missao_id=None, order_id=None):
        try:
            url = f"{self.base_url}/agv/status"
            payload = {
                'agv_id': self.agv_id,
                'status': {
                    'estado': estado,
                    'detalhe': detalhe,
                    'qr': qr,
                    'missaoId': missao_id,
                    'orderId': order_id
                }
            }
            requests.post(url, json=payload, timeout=3)
        except Exception:
            pass

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
            # Alguns endpoints retornam as TAGs agregadas também
            tags_agregadas = pedido.get('tag') or pedido.get('tags')  # compat possível
            tags_lista = tags_agregadas.split(',') if tags_agregadas else []

            for i, item_nome in enumerate(itens_lista):
                corredor = corredores[i] if i < len(corredores) else '1'
                subcorredor = subcorredores[i] if i < len(subcorredores) else '1'

                chave = f"{corredor}_{subcorredor}"

                if chave not in itens_por_subcorredor:
                    itens_por_subcorredor[chave] = []

                itens_por_subcorredor[chave].append({
                    'nome': item_nome.strip(),
                    'corredor': corredor,
                    'subcorredor': subcorredor,
                    'tag': (tags_lista[i].strip() if i < len(tags_lista) else None)
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
        """Navegar até o QR code do subcorredor usando navegação por linha"""
        # Formatar para o padrão do usuário nos logs
        try:
            cc, ss = subcorredor_destino.split('_', 1)
            destino_label = f"Corredor{cc}_SubCorredor{ss}"
        except Exception:
            destino_label = subcorredor_destino
        print(f"🧭 Navegando até subcorredor: {destino_label}")

        # Usar navegação por linha para encontrar interseção
        qr_encontrado = self.line_navigation.navigate_to_intersection(subcorredor_destino)

        if not qr_encontrado:
            print(f"❌ Não foi possível encontrar o subcorredor {subcorredor_destino}")
            return False

        # QR encontrado! Entrar no subcorredor usando APENAS o processo azul->verde (sem avanço fixo/giroscópio)
        print("✅ Subcorredor encontrado, entrando com rotina azul→verde (visão)")
        ok = self.line_navigation.go_until_blue_then_turn_right_until_green(
            drive_speed=22,
            turn_speed_fast=35,
            turn_speed_slow=14,
            timeout_drive=25.0,
            timeout_turn=15.0,
            min_turn_time_s=1.2,
            green_persist_frames=3,
            green_min_area=1800,
            turn_direction='direita',
            scan_shelf_qr_after_turn=True,
            shelf_cam_index=0,
            shelf_scan_time_s=3.0,
            shelf_scan_debug=False,
            shelf_expected_qr=destino_label,
            # Não avançar após verde/QR e não alinhar: parar já quando verde estiver centralizado
            align_after_turn=False,
            post_match_forward_s=0.0,
            post_match_forward_speed=0,
            require_centered_green=True,
            green_center_tol_px=40,
        )
        if not ok:
            print("❌ Falha na rotina azul→verde para entrar no subcorredor")
            return False

        return True

    def loop_missoes(self):
        """Loop simples: busca próximo comando e executa ida ao subcorredor."""
        print("🔄 Loop de missões iniciado (polling /agv/next_command)")
        while not self._mission_loop_stop.is_set():
            cmd = self.obter_proximo_comando()
            if not cmd:
                # Dorme pouco e verifica se deve parar
                for _ in range(20):
                    if self._mission_loop_stop.is_set():
                        break
                    time.sleep(0.1)
                continue

            missao_id = cmd.get('id')
            order_id = cmd.get('order_id')
            itens = cmd.get('items') or []
            if not itens:
                self.reportar_status('erro', detalhe='Comando sem itens', missao_id=missao_id)
                continue

            # Como sua maquete tem dois subcorredores em sequência, vamos ao primeiro destino do primeiro item
            loc = itens[0].get('location', {})
            corredor = int(loc.get('corredor', 1))
            subc = int(loc.get('sub_corredor', 1))
            destino_code = f"{corredor:02d}_{subc:02d}"
            destino_label = f"Corredor{corredor:02d}_SubCorredor{subc:02d}"
            print(f"🎯 Missão recebida {missao_id}: ir ao subcorredor {destino_label}")
            self.reportar_status('indo_para_corredor', detalhe=destino_label, missao_id=missao_id, order_id=order_id)

            ok = self._navegar_ate_subcorredor(destino_code)
            if not ok:
                self.reportar_status('erro', detalhe=f'Falha na navegacao {destino_label}', missao_id=missao_id, order_id=order_id)
                continue

            self.reportar_status('no_corredor', detalhe=destino_label, missao_id=missao_id, order_id=order_id)
            print("✅ No corredor. (coleta pode ser adicionada depois). Marcando pedido como concluído para fluxo simples.")
            # Para fluxo simples da maquete, concluímos a missão após chegar ao corredor
            self.reportar_status('concluida', detalhe=destino_label, missao_id=missao_id, order_id=order_id)
            for _ in range(10):
                if self._mission_loop_stop.is_set():
                    break
                time.sleep(0.1)

        print("🛑 Loop de missões finalizado")

    def iniciar_loop_missoes(self):
        if self._mission_loop_thread and self._mission_loop_thread.is_alive():
            print("⚠️ Loop de missões já está em execução")
            return
        self._mission_loop_stop.clear()
        self._mission_loop_thread = threading.Thread(target=self.loop_missoes, daemon=True)
        self._mission_loop_thread.start()
        print("▶️ Loop de missões iniciado em segundo plano")

    def parar_loop_missoes(self):
        if not self._mission_loop_thread:
            print("ℹ️ Loop de missões não está em execução")
            return
        print("⏹️ Parando loop de missões...")
        self._mission_loop_stop.set()
        self._mission_loop_thread.join(timeout=3)
        self._mission_loop_thread = None
        print("✅ Loop de missões parado")

    def _coletar_itens_subcorredor(self, subcorredor):
        """Coletar todos os itens do subcorredor usando QR codes"""
        print(f"🤖 Iniciando coleta no subcorredor: {subcorredor}")

        itens_subcorredor = self.missao_ativa['itens_por_subcorredor'].get(subcorredor, [])

        for item in itens_subcorredor:
            print(f"📦 Procurando item: {item['nome']}")

            # Definir QR esperado do item com base em TAG numérica do cadastro (formato TAG0001)
            qr_item_esperado = self._format_expected_item_tag(item.get('tag'), item['nome'])
            print(f"🔍 Procurando QR code do item (esperado): {qr_item_esperado}")

            qr_detectado = None
            tentativas_item = 0
            max_tentativas_item = 5

            while qr_detectado != qr_item_esperado and tentativas_item < max_tentativas_item:
                try:
                    # Preferir uma varredura de múltiplos QRs com a câmera 0 (mesma rotina da estante)
                    results = []
                    try:
                        results = self.line_navigation._scan_shelf_qr_secondary_camera(
                            camera_index=0,
                            duration_s=1.5,
                            debug=False,
                            debug_dir=None,
                            debug_prefix='item_qr'
                        ) or []
                    except Exception as e_scan:
                        print(f"⚠️ Falha no scan multi-QR: {e_scan}")

                    # Tentar casar o esperado entre os encontrados
                    if results:
                        encontrados = []
                        for r in results:
                            data_raw = r.get('data')
                            if not data_raw:
                                continue
                            norm = self._normalize_qr_code(data_raw)
                            encontrados.append(norm)
                            if norm == qr_item_esperado:
                                qr_detectado = norm
                                print(f"✅ Item encontrado na varredura: {norm}")
                                break
                        if qr_detectado == qr_item_esperado:
                            break
                        else:
                            print(f"⚠️ QRs visíveis: {', '.join(encontrados)} — ainda não achou {qr_item_esperado}")
                    else:
                        print("📷 Nenhum QR code na varredura atual")

                    # Se não encontrou na varredura, tentar leitura única como fallback
                    qr_resultado = self.qr_detector.detectar_qr_code()
                    if qr_resultado and qr_resultado.get('detectado'):
                        raw = qr_resultado.get('codigo')
                        norm = self._normalize_qr_code(raw)
                        print(f"📷 (fallback) QR detectado: {raw} (normalizado: {norm})")
                        if norm == qr_item_esperado:
                            qr_detectado = norm
                            print("✅ Item encontrado no fallback!")
                            break
                        else:
                            print(f"⚠️ (fallback) QR errado: {norm} (esperado: {qr_item_esperado})")

                    # Pequeno movimento para procurar melhor enquadramento
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

        # Sair do subcorredor usando navegação por linha
        print("⬅️ Saindo do subcorredor")
        if not self.line_navigation.exit_subcorredor():
            print("❌ Falha ao sair do subcorredor")
            return False

        return True

    def _format_expected_item_tag(self, raw_tag, item_nome: str) -> str:
        """Formata a TAG esperada no padrão 'TAG' + dígitos (mín. 4 com zero à esquerda).
        Se não houver tag no cadastro, utiliza fallback antigo baseado no nome.
        """
        if raw_tag is not None:
            s = str(raw_tag).strip().upper()
            # Extrair apenas dígitos da tag (suporta cases como 'TAG12', '0012', '12')
            digits = ''.join(ch for ch in s if ch.isdigit())
            if digits:
                # Preencher para pelo menos 4 dígitos sem cortar números maiores
                digits_padded = digits if len(digits) >= 4 else digits.zfill(4)
                return f"TAG{digits_padded}"
        # Fallback: manter compatibilidade antiga (não numérico)
        print("⚠️ Tag numérica ausente/indefinida no item; usando fallback baseado no nome.")
        return f"TAG{item_nome.replace(' ', '')[:4].upper()}"

    def _normalize_qr_code(self, code: str) -> str:
        """Normaliza qualquer leitura de QR para o padrão TAG + dígitos (mín. 4).
        Exemplos: '123' -> 'TAG0123'; 'TAG7' -> 'TAG0007'; 'tag-1234' -> 'TAG1234'.
        Se não achar dígitos, retorna o texto original upper.
        """
        if code is None:
            return ''
        s = str(code).strip().upper()
        digits = ''.join(ch for ch in s if ch.isdigit())
        if digits:
            digits_padded = digits if len(digits) >= 4 else digits.zfill(4)
            return f"TAG{digits_padded}"
        return s

    def _ir_ate_entrega(self):
        """Ir até o ponto de entrega usando navegação por linha"""
        print("📦 Indo para ponto de entrega")

        # Usar navegação por linha para encontrar ponto de entrega
        if not self.line_navigation.navigate_to_delivery_point():
            print("❌ Não foi possível chegar ao ponto de entrega")
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

    # Configurações do config.json
    pc_ip = get_config('backend.ip')
    pc_port = get_config('backend.port')
    esp32_port = get_config('esp32.port')

    print(f"📡 Backend: {pc_ip}:{pc_port}")
    print(f"🤖 ESP32: {esp32_port}")

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
        print("6. Iniciar loop de missões (polling)")
        print("7. Parar loop de missões")
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
                    # Ajuda: buscar automaticamente um comando pendente
                    print("🔎 Verificando se há pedido pendente...")
                    cmd = agv.obter_proximo_comando()
                    if cmd and cmd.get('items'):
                        print("✅ Pedido pendente encontrado e iniciado como 'em_andamento'.")
                        print(f"   Pedido #{cmd.get('order_id')} | Itens: {len(cmd.get('items', []))}")
                        print("   Dica: use a opção 6 para iniciar o loop de missões e navegar até o subcorredor.")
                    else:
                        print("ℹ️ Nenhum comando pendente. Crie um pedido no site/app e tente novamente.")

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

            elif opcao == '6':
                agv.iniciar_loop_missoes()

            elif opcao == '7':
                agv.parar_loop_missoes()

            elif opcao == '0':
                agv.navigation.parar()
                print("👋 Saindo...")
                break

            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            agv.navigation.parar()
            agv.parar_loop_missoes()
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            agv.navigation.parar()
            agv.parar_loop_missoes()

if __name__ == "__main__":
    main()