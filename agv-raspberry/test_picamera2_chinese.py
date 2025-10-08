#!/usr/bin/env python3
"""
Teste de câmera chinesa CSI usando Picamera2 (biblioteca oficial)
Esta é a forma CORRETA de usar câmeras chinesas CSI no Raspberry Pi 5
"""

import cv2
import os
from picamera2 import Picamera2

def test_picamera2_basic():
    """Teste básico com Picamera2"""
    print("📷 TESTE PICAMERA2 - CÂMERA CHINESA CSI")
    print("======================================")

    try:
        # Inicializar câmera
        print("Inicializando Picamera2...")
        picam2 = Picamera2()

        # Configurar para preview
        config = picam2.create_preview_configuration(
            main={"format": 'XRGB8888', "size": (640, 480)}
        )
        picam2.configure(config)

        print("Iniciando câmera...")
        picam2.start()

        # Aguardar estabilização
        import time
        time.sleep(2)

        # Capturar frame
        print("Capturando imagem...")
        frame = picam2.capture_array()

        # Converter formato (XRGB para BGR)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Salvar imagem
        filename = "teste_picamera2.jpg"
        cv2.imwrite(filename, frame_bgr)

        height, width = frame_bgr.shape[:2]
        print("✅ Imagem capturada com sucesso!")
        print(f"   📁 Arquivo: {filename}")
        print(f"   📐 Resolução: {width}x{height}")

        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   📊 Tamanho: {size} bytes")

        # Parar câmera
        picam2.stop()
        print("✅ Câmera parada")

        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def create_picamera2_test_script():
    """Cria script interativo para testar Picamera2"""
    script_content = '''#!/usr/bin/env python3
"""
Script interativo para testar câmera chinesa CSI com Picamera2
Clique na imagem para tirar foto, pressione 'q' para sair
"""

import cv2
import os
from picamera2 import Picamera2

# Criar pasta para imagens
if not os.path.exists("validacao"):
    os.makedirs("validacao")

# Inicializar câmera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": 'XRGB8888', "size": (640, 480)}
))
picam2.start()

print("🎥 Câmera inicializada. Clique na imagem para tirar foto, 'q' para sair")

# Função para capturar imagem
def capturar_imagem(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        nome_arquivo = f"validacao/imagemValidacao_{len(os.listdir('validacao')) + 1}.jpg"
        cv2.imwrite(nome_arquivo, frame)
        print(f"📷 Imagem salva: {nome_arquivo}")

# Criar janela
cv2.namedWindow("Camera Picamera2")
cv2.setMouseCallback("Camera Picamera2", capturar_imagem)

try:
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.imshow("Camera Picamera2", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\\n🛑 Interrompido pelo usuário")

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    print("✅ Câmera finalizada")
'''

    try:
        with open('test_picamera2_interactive.py', 'w') as f:
            f.write(script_content)
        os.chmod('test_picamera2_interactive.py', 0o755)
        print("✅ Script interativo criado: test_picamera2_interactive.py")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        return False

def main():
    """Função principal"""
    print("🎥 TESTE PICAMERA2 - CÂMERA CHINESA CSI")
    print("======================================")
    print("Usando a biblioteca OFICIAL do Raspberry Pi")
    print()

    # Teste básico
    success = test_picamera2_basic()

    # Criar script interativo
    script_created = create_picamera2_test_script()

    print("\n📊 RESUMO:")
    print(f"Teste básico: {'✅ OK' if success else '❌ FALHA'}")
    print(f"Script criado: {'✅ OK' if script_created else '❌ FALHA'}")

    if success:
        print("\n🎉 CÂMERA CHINESA FUNCIONANDO COM PICAMERA2!")
        print("\n💡 Para usar no seu código AGV:")
        print("   from picamera2 import Picamera2")
        print("   picam2 = Picamera2()")
        print("   picam2.configure(picam2.create_preview_configuration(main={'format': 'XRGB8888', 'size': (640, 480)}))")
        print("   picam2.start()")
        print("   frame = picam2.capture_array()")
        print("   # Converter: frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)")

        print("\n🖱️  Para teste interativo:")
        print("   python3 test_picamera2_interactive.py")

if __name__ == "__main__":
    main()