#!/usr/bin/env python3
"""
Script para testar leitura de QR codes com câmera
Requer: pip install opencv-python pyzbar
"""

import cv2
import numpy as np
import time
import sys

def test_qr_code_reading():
    """Testa leitura de QR codes"""
    print("📱 TESTANDO LEITURA DE QR CODES")
    print("=" * 50)

    try:
        import pyzbar.pyzbar as pyzbar
        print("✅ pyzbar importado com sucesso")
    except ImportError:
        print("❌ pyzbar não instalado")
        print("💡 Instale com: pip install pyzbar")
        print("   ou: pip install pyzbar[scripts]")
        return False

    # Criar QR code de teste
    print("\n🆔 Criando QR code de teste...")
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data("AGV-TEST-001")
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save("teste_qr_code.png")
        print("✅ QR code criado: teste_qr_code.png")
        print("   Conteúdo: AGV-TEST-001")
    except ImportError:
        print("❌ qrcode não instalado (pip install qrcode[pil])")
        print("   Criando QR code manualmente...")
        # Criar imagem simples com texto
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[:] = [255, 255, 255]
        cv2.putText(img, "AGV-TEST-001", (10, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.imwrite("teste_qr_code.png", img)
        print("✅ Imagem de teste criada (não é QR code real)")

    # Testar câmera
    print("\n📷 Procurando câmera...")
    cap = None
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ Câmera encontrada no índice {i}")
            break
        cap.release()

    if not cap or not cap.isOpened():
        print("❌ Nenhuma câmera encontrada")
        return False

    print("\n🎯 Iniciando detecção de QR codes...")
    print("   Mostre um QR code para a câmera")
    print("   Pressione 'q' para sair")

    qr_detected = False
    start_time = time.time()

    try:
        while time.time() - start_time < 30:  # 30 segundos timeout
            ret, frame = cap.read()
            if not ret:
                print("❌ Erro ao capturar frame")
                break

            # Detectar QR codes
            decoded_objects = pyzbar.decode(frame)

            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    qr_type = obj.type

                    print(f"\n🎉 QR Code detectado!")
                    print(f"   Tipo: {qr_type}")
                    print(f"   Dados: {qr_data}")

                    # Desenhar retângulo ao redor do QR
                    points = obj.polygon
                    if len(points) > 4:
                        hull = cv2.convexHull(np.array([point for point in points], dtype=np.int32))
                        cv2.polylines(frame, [hull], True, (0, 255, 0), 3)
                    else:
                        cv2.polylines(frame, [np.array(points, dtype=np.int32)], True, (0, 255, 0), 3)

                    qr_detected = True

            # Adicionar texto na tela
            cv2.putText(frame, "Mostre um QR code", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Pressione 'q' para sair", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Mostrar frame
            cv2.imshow('QR Code Scanner', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if qr_detected:
        print("\n✅ Teste de QR code bem-sucedido!")
        return True
    else:
        print("\n⚠️  Nenhum QR code detectado no tempo limite")
        print("💡 Certifique-se de que:")
        print("   1. A câmera está focada no QR code")
        print("   2. Há boa iluminação")
        print("   3. O QR code está dentro do campo de visão")
        return False

def create_qr_integration_example():
    """Cria exemplo de integração com o sistema AGV"""
    example_code = '''#!/usr/bin/env python3
"""
Exemplo de integração de leitura de QR codes no sistema AGV
"""

import cv2
import pyzbar.pyzbar as pyzbar
import time
import logging

class QRCodeReader:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False

    def start(self):
        """Inicia leitura de QR codes"""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            logging.error("Não foi possível abrir câmera")
            return False

        self.is_running = True
        logging.info("Leitor de QR codes iniciado")
        return True

    def stop(self):
        """Para leitura"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def read_qr_code(self, timeout=10):
        """Lê um QR code com timeout"""
        if not self.cap or not self.cap.isOpened():
            return None

        start_time = time.time()
        while self.is_running and (time.time() - start_time) < timeout:
            ret, frame = self.cap.read()
            if not ret:
                continue

            decoded_objects = pyzbar.decode(frame)
            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    logging.info(f"QR Code detectado: {qr_data}")
                    return qr_data

            time.sleep(0.1)

        return None

    def scan_item_location(self, item_id):
        """Escaneia localização de um item"""
        logging.info(f"Escaneando localização do item {item_id}")

        # Simular movimento até a posição do item
        # self.agv.move_to_item_location(item_id)

        # Ler QR code da localização
        qr_data = self.read_qr_code(timeout=30)

        if qr_data:
            # Processar dados do QR (posição x,y, corredor, etc.)
            location_data = self.parse_location_qr(qr_data)
            logging.info(f"Localização encontrada: {location_data}")
            return location_data
        else:
            logging.warning("QR code de localização não encontrado")
            return None

    def parse_location_qr(self, qr_data):
        """Parse dos dados do QR code de localização"""
        # Formato esperado: "LOC:X=1.5,Y=2.3,CORREDOR=A,SUB=1"
        try:
            data = {}
            parts = qr_data.replace("LOC:", "").split(",")
            for part in parts:
                key, value = part.split("=")
                data[key.lower()] = value
            return data
        except:
            return {"raw": qr_data}

# Exemplo de uso no sistema AGV
def example_agv_qr_integration():
    """Exemplo de integração"""
    qr_reader = QRCodeReader(camera_index=0)

    if qr_reader.start():
        try:
            # Escanear item solicitado
            item_location = qr_reader.scan_item_location("ITEM001")

            if item_location:
                # Mover AGV para a localização
                print(f"Movendo para: {item_location}")

                # Simular movimento
                # agv.move_to(float(item_location['x']), float(item_location['y']))

                # Confirmar entrega
                print("Item localizado com sucesso!")
            else:
                print("Falha ao localizar item")

        finally:
            qr_reader.stop()

if __name__ == "__main__":
    example_agv_qr_integration()
'''

    with open('qr_code_integration_example.py', 'w') as f:
        f.write(example_code)

    print("✅ Exemplo de integração criado: qr_code_integration_example.py")

def main():
    """Função principal"""
    print("📱 TESTE DE QR CODES - SISTEMA AGV")
    print("=" * 50)

    # Testar leitura de QR codes
    success = test_qr_code_reading()

    # Criar exemplo de integração
    create_qr_integration_example()

    # Resumo
    print("\n📊 RESUMO DO TESTE DE QR CODES")
    print("=" * 50)
    print(f"Leitura de QR codes: {'✅ OK' if success else '❌ FALHA'}")

    if success:
        print("\n🎉 QR codes funcionando!")
        print("\n💡 INTEGRAÇÃO NO SISTEMA AGV:")
        print("   1. Importe QRCodeReader no main.py")
        print("   2. Use para localizar itens no armazém")
        print("   3. Implemente navegação baseada em QR codes")
        print("   4. Veja exemplo em: qr_code_integration_example.py")
    else:
        print("\n❌ Problemas com QR codes")
        print("\n🔧 SOLUÇÕES:")
        print("   1. pip install pyzbar qrcode[pil]")
        print("   2. Teste câmera primeiro: python3 test_camera.py")
        print("   3. Verifique iluminação e foco")
        print("   4. Teste com QR codes simples")

if __name__ == "__main__":
    main()