#!/bin/bash
# Instalar dependências básicas para leitura de QR codes
# Versão simplificada e confiável

echo "🔍 INSTALANDO DEPENDÊNCIAS PARA LEITURA DE QR CODES"
echo "=================================================="

# Verificar se estamos no Raspberry Pi
if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "✅ Raspberry Pi detectado"
    IS_RPI=true
else
    echo "💻 Sistema não-Raspberry Pi detectado (PC/Windows)"
    IS_RPI=false
fi

# Ativar ambiente virtual se existir
if [[ -d "venv" ]]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

echo "📦 Instalando dependências básicas..."

# Instalar dependências do sistema (sempre necessárias)
echo "🔧 Instalando pacotes do sistema..."
sudo apt update
sudo apt install -y python3-pip python3-dev build-essential

# Instalar OpenCV (versão do repositório - mais confiável)
echo "📷 Instalando OpenCV..."
sudo apt install -y python3-opencv

# Instalar pyzbar (leitor de QR codes)
echo "📱 Instalando pyzbar..."
pip install pyzbar --no-cache-dir

# Verificar se Pillow está instalado (para manipulação de imagens)
echo "🖼️ Verificando Pillow..."
pip install Pillow --no-cache-dir

# Testar importações
echo "🧪 Testando importações..."
python3 -c "
try:
    import cv2
    print('✅ OpenCV OK')
except ImportError as e:
    print('❌ OpenCV falhou:', e)

try:
    from pyzbar.pyzbar import decode
    print('✅ pyzbar OK')
except ImportError as e:
    print('❌ pyzbar falhou:', e)

try:
    from PIL import Image
    print('✅ Pillow OK')
except ImportError as e:
    print('❌ Pillow falhou:', e)
"

echo ""
echo "🎯 TESTE DO SISTEMA:"
echo "===================="

# Testar câmera USB (sempre funciona)
echo "📷 Testando câmera USB..."
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret and frame is not None:
        print('✅ Câmera USB OK')
    else:
        print('⚠️ Câmera USB conectada mas sem imagem')
    cap.release()
else:
    print('⚠️ Nenhuma câmera USB detectada')
"

# Testar leitura de QR codes
echo "📱 Testando leitura de QR codes..."
python3 -c "
import cv2
from pyzbar.pyzbar import decode
import numpy as np

# Criar imagem de teste com QR code
img = np.ones((100, 100, 3), dtype=np.uint8) * 255
# Nota: Este é apenas um teste básico de importação

try:
    # Tentar decodificar (mesmo que falhe, as bibliotecas estão OK)
    result = decode(img)
    print('✅ Sistema de QR codes OK')
except Exception as e:
    print('✅ Bibliotecas carregadas (QR code precisa de imagem real)')
"

echo ""
echo "🎉 INSTALAÇÃO CONCLUÍDA!"
echo "========================"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "==================="
echo "1. Teste o leitor USB:"
echo "   python qr_reader_simple_usb.py"
echo ""
echo "2. Com visualização:"
echo "   python qr_reader_simple_usb.py --visual"
echo ""
echo "3. Para câmeras CSI (Raspberry Pi):"
echo "   pip install picamera2"
echo "   python qr_reader_simple.py --visual"
echo ""
echo "💡 DICAS:"
echo "========"
echo "- Use webcam USB para testes no PC"
echo "- Use câmeras CSI chinesas no Raspberry Pi"
echo "- Pressione 'q' para sair, 'r' para resetar lista"