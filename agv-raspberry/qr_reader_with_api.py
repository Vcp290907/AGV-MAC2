#!/usr/bin/env python3
"""
Leitor de QR Codes com API do PC
Conecta ao banco via HTTP (não SQLite direto)
Permite comunicação em tempo real com o PC
"""

from picamera2 import Picamera2
from pyzbar import pyzbar
import cv2
import requests
import json
import time
import sys
from datetime import datetime

class QRReaderWithAPI:
    """Leitor de QR codes que se conecta à API do PC"""

    def __init__(self, pc_ip="192.168.0.100", pc_port=5000):
        self.pc_ip = pc_ip
        self.pc_port = pc_port
        self.base_url = f"http://{pc_ip}:{pc_port}"
        self.qr_codes_detectados = set()
        self.picam2 = None

    def testar_conexao_api(self):
        """Testar conexão com a API do PC"""
        try:
            print(f"🔗 Testando conexão com API do PC: {self.base_url}")
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                print("✅ Conexão com API estabelecida!")
                return True
            else:
                print(f"❌ API respondeu com status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão com API: {e}")
            print("💡 Verifique se o backend Flask está rodando no PC")
            return False

    def consultar_item_por_tag(self, tag):
        """Consultar item via API do PC"""
        try:
            # Usar endpoint de itens com pesquisa
            response = requests.get(f"{self.base_url}/itens", timeout=5)

            if response.status_code == 200:
                itens = response.json()

                # Procurar item pela tag
                for item in itens:
                    if item.get('tag') == tag:
                        return item

            return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao consultar API: {e}")
            return None

    def consultar_localizacao(self, qr_data):
        """Consultar localização baseada no conteúdo do QR"""
        # Tentar diferentes formatos de QR code

        # Formato: Corredor_01/SubCorredor_02
        if '/' in qr_data and 'Corredor' in qr_data:
            try:
                partes = qr_data.split('/')
                corredor_part = partes[0]  # "Corredor_01"
                subcorredor_part = partes[1]  # "SubCorredor_02"

                corredor = corredor_part.replace('Corredor_', '')
                subcorredor = subcorredor_part.replace('SubCorredor_', '')

                return {
                    'tipo': 'localizacao',
                    'corredor': corredor,
                    'sub_corredor': subcorredor,
                    'descricao': f"Localização: Corredor {corredor}, Sub-corredor {subcorredor}"
                }
            except:
                pass

        # Formato: TAG0001, TAG0002, etc.
        if qr_data.startswith('TAG') and len(qr_data) >= 7:
            item = self.consultar_item_por_tag(qr_data)
            if item:
                return {
                    'tipo': 'item',
                    'item': item,
                    'descricao': f"Item: {item['nome']} (Tag: {item['tag']})"
                }

        # Outros formatos - tentar como tag diretamente
        item = self.consultar_item_por_tag(qr_data)
        if item:
            return {
                'tipo': 'item',
                'item': item,
                'descricao': f"Item: {item['nome']} (Tag: {item['tag']})"
            }

        # Não encontrado
        return {
            'tipo': 'desconhecido',
            'dados': qr_data,
            'descricao': f"QR Code não identificado: {qr_data}"
        }

    def enviar_status_para_pc(self, qr_data, info):
        """Enviar status da detecção para o PC (opcional)"""
        try:
            dados_status = {
                'tipo': 'qr_detectado',
                'qr_data': qr_data,
                'info': info,
                'timestamp': datetime.now().isoformat(),
                'raspberry_ip': '192.168.0.200'  # IP do Raspberry
            }

            # Tentar enviar para endpoint de status (se existir)
            response = requests.post(
                f"{self.base_url}/raspberry/status",
                json=dados_status,
                timeout=2
            )

            if response.status_code == 200:
                print("📤 Status enviado para PC")
            else:
                # Não é erro crítico se não conseguir enviar
                pass

        except requests.exceptions.RequestException:
            # Não mostrar erro - é opcional
            pass

    def mostrar_informacoes_qr(self, qr_data, info):
        """Mostrar informações detalhadas do QR code"""
        print(f"\n🎯 QR CODE DETECTADO: {qr_data}")
        print("=" * 50)
        print(f"📝 Descrição: {info['descricao']}")

        if info['tipo'] == 'item':
            item = info['item']
            print(f"📦 Nome: {item['nome']}")
            print(f"🏷️ Tag: {item['tag']}")
            print(f"📂 Categoria: {item['categoria']}")
            print(f"📍 Localização: Corredor {item.get('corredor', 'N/A')}, Sub {item.get('sub_corredor', 'N/A')}, Pos {item.get('posicao_x', 'N/A')}")
            print(f"✅ Disponível: {'Sim' if item.get('disponivel', True) else 'Não'}")

        elif info['tipo'] == 'localizacao':
            print(f"🏢 Corredor: {info['corredor']}")
            print(f"🚪 Sub-corredor: {info['sub_corredor']}")

        else:
            print(f"❓ Tipo: Desconhecido")
            print(f"📄 Dados brutos: {info['dados']}")

        print(f"🕒 Detectado em: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)

    def initialize_camera(self):
        """Inicializar câmera CSI"""
        print("📷 Inicializando câmera CSI...")

        try:
            self.picam2 = Picamera2(camera_num=0)
            self.picam2.configure(self.picam2.create_preview_configuration(
                main={"format": 'XRGB8888', "size": (1920, 1080)}
            ))
            self.picam2.start()
            print("✅ Câmera CSI inicializada!")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar câmera: {e}")
            return False

    def run(self):
        """Executar leitura de QR codes com consulta à API"""
        print("🔍 LEITOR DE QR CODES COM API DO PC")
        print("=" * 50)
        print(f"🔗 Conectando ao PC: {self.base_url}")
        print("Pressione 'q' para sair")
        print("O sistema irá consultar a API do PC automaticamente\n")

        # Testar conexão com API
        if not self.testar_conexao_api():
            print("❌ Não foi possível conectar à API do PC")
            print("💡 Certifique-se de que o backend Flask está rodando no PC")
            return

        if not self.initialize_camera():
            return

        try:
            while True:
                # Capturar frame
                frame = self.picam2.capture_array()

                # Processamento de imagem (igual ao código do usuário)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)

                # Detectar QR codes
                decoded_objects = pyzbar.decode(enhanced)

                # Processar detecções
                for obj in decoded_objects:
                    data = obj.data.decode('utf-8')

                    # Só processar se não foi detectado recentemente
                    if data not in self.qr_codes_detectados:
                        self.qr_codes_detectados.add(data)

                        # Consultar informações via API
                        info = self.consultar_localizacao(data)

                        # Mostrar informações detalhadas
                        self.mostrar_informacoes_qr(data, info)

                        # Enviar status para PC (opcional)
                        self.enviar_status_para_pc(data, info)

                    # Desenhar retângulo (sempre)
                    (x, y, w, h) = obj.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Mostrar estatísticas na tela
                api_status = "API: OK" if self.testar_conexao_api() else "API: OFFLINE"
                stats_text = f"QR Codes detectados: {len(self.qr_codes_detectados)} | {api_status}"
                cv2.putText(frame, stats_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Mostrar frame
                cv2.imshow("Leitor de QR Code com API do PC", frame)

                # Verificar tecla
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")

        finally:
            if self.picam2:
                self.picam2.stop()
            cv2.destroyAllWindows()

            # Resumo final
            print(f"\n📊 RESUMO FINAL:")
            print(f"   Total de QR codes únicos detectados: {len(self.qr_codes_detectados)}")
            if self.qr_codes_detectados:
                print("   QR codes detectados:")
                for i, qr_data in enumerate(sorted(self.qr_codes_detectados), 1):
                    print(f"   {i}. {qr_data}")

def main():
    """Função principal"""
    print("🎯 LEITOR QR + API DO PC")
    print("=" * 30)

    # Configurações padrão
    pc_ip = "192.168.0.100"  # IP do PC
    pc_port = 5000

    # Verificar argumentos
    if len(sys.argv) >= 2:
        pc_ip = sys.argv[1]
    if len(sys.argv) >= 3:
        pc_port = int(sys.argv[2])

    print(f"🔗 Conectando ao PC: {pc_ip}:{pc_port}")

    # Executar leitor
    reader = QRReaderWithAPI(pc_ip=pc_ip, pc_port=pc_port)
    reader.run()

if __name__ == "__main__":
    main()