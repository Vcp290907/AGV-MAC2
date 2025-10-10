#!/usr/bin/env python3
"""
Leitor de QR Codes com Integração ao Banco de Dados
Lê QR codes e consulta informações no banco de dados do AGV
"""

from picamera2 import Picamera2
from pyzbar import pyzbar
import cv2
import sqlite3
import os
import sys
from datetime import datetime

class QRReaderWithDatabase:
    """Leitor de QR codes integrado com banco de dados"""

    def __init__(self, db_path="../agv-web/backend/agv_system.db"):
        self.db_path = db_path
        self.qr_codes_detectados = set()
        self.picam2 = None

    def conectar_banco(self):
        """Conectar ao banco de dados"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Banco de dados não encontrado: {self.db_path}")
                return None

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ Erro ao conectar banco: {e}")
            return None

    def consultar_item_por_tag(self, tag):
        """Consultar item no banco por tag"""
        conn = self.conectar_banco()
        if not conn:
            return None

        try:
            # Consultar por tag exata
            item = conn.execute('''
                SELECT id, nome, tag, categoria, corredor, sub_corredor,
                       posicao_x, posicao_y, disponivel
                FROM itens
                WHERE tag = ?
            ''', (tag,)).fetchone()

            conn.close()

            if item:
                return dict(item)
            else:
                return None

        except Exception as e:
            print(f"❌ Erro ao consultar item: {e}")
            conn.close()
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
            print(f"📍 Localização: Corredor {item['corredor']}, Sub {item['sub_corredor']}, Pos {item['posicao_x']}")
            print(f"✅ Disponível: {'Sim' if item['disponivel'] else 'Não'}")

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
        """Executar leitura de QR codes com consulta ao banco"""
        print("🔍 LEITOR DE QR CODES COM BANCO DE DADOS")
        print("=" * 50)
        print("Pressione 'q' para sair")
        print("O sistema irá consultar informações no banco de dados\n")

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

                        # Consultar informações no banco
                        info = self.consultar_localizacao(data)

                        # Mostrar informações detalhadas
                        self.mostrar_informacoes_qr(data, info)

                    # Desenhar retângulo (sempre)
                    (x, y, w, h) = obj.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Mostrar estatísticas na tela
                stats_text = f"QR Codes detectados: {len(self.qr_codes_detectados)}"
                cv2.putText(frame, stats_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Mostrar frame
                cv2.imshow("Leitor de QR Code com Banco de Dados", frame)

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
    print("🎯 LEITOR QR + BANCO DE DADOS")
    print("=" * 35)

    # Verificar se banco existe
    db_path = "../agv-web/backend/agv_system.db"
    if not os.path.exists(db_path):
        print(f"⚠️ Banco de dados não encontrado em: {db_path}")
        print("💡 Execute o backend Flask primeiro para criar o banco")
        return

    # Executar leitor
    reader = QRReaderWithDatabase(db_path)
    reader.run()

if __name__ == "__main__":
    main()