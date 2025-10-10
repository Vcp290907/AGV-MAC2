#!/bin/bash
# Correção completa para picamera2 no Raspberry Pi OS Bookworm
# Resolve problemas de PEP 668 e dependências

echo "🔧 CORREÇÃO PICAMERA2 - RASPBERRY PI OS BOOKWORM"
echo "================================================"

# Verificar se estamos no Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "❌ Este script é apenas para Raspberry Pi"
    exit 1
fi

echo "✅ Raspberry Pi detectado"

# Verificar versão do sistema
if grep -q "bookworm" /etc/os-release; then
    echo "📖 Raspberry Pi OS Bookworm detectado"
    IS_BOOKWORM=true
else
    echo "📖 Raspberry Pi OS antigo detectado"
    IS_BOOKWORM=false
fi

# 1. Instalar dependências do sistema
echo "📦 Instalando dependências do sistema..."
sudo apt update
sudo apt install -y python3-pip python3-dev build-essential
sudo apt install -y libcap-dev python3-prctl libcamera-dev
sudo apt install -y python3-libcamera python3-picamera2

# 2. Verificar se ambiente virtual existe
if [[ -d "venv" ]]; then
    echo "🐍 Ambiente virtual encontrado"
    source venv/bin/activate
else
    echo "🐍 Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 3. Instalar picamera2 (método correto para Bookworm)
echo "📷 Instalando picamera2..."
if [[ "$IS_BOOKWORM" == true ]]; then
    # Método para Bookworm - usar --break-system-packages
    echo "📖 Usando método Bookworm..."
    pip install picamera2 --break-system-packages
else
    # Método para versões antigas
    echo "📖 Usando método antigo..."
    pip install picamera2
fi

# 4. Verificar instalação
echo "🧪 Testando picamera2..."
python3 -c "
try:
    from picamera2 import Picamera2
    print('✅ picamera2 OK - import funciona')

    # Testar inicialização básica
    try:
        picam2 = Picamera2()
        print('✅ picamera2 OK - inicialização funciona')
        picam2.close()
    except Exception as e:
        print(f'⚠️ picamera2 import OK, mas inicialização falhou: {e}')
        print('💡 Isso pode ser normal se não houver câmera conectada')

except ImportError as e:
    print(f'❌ picamera2 falhou: {e}')
    exit 1
"

# 5. Testar câmera CSI
echo "📷 Testando câmera CSI..."
python3 -c "
from picamera2 import Picamera2
import time

try:
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={'format': 'XRGB8888', 'size': (640, 480)})
    picam2.configure(config)
    picam2.start()
    time.sleep(2)

    frame = picam2.capture_array()
    if frame is not None:
        print('✅ Câmera CSI OK - captura funcionando')
    else:
        print('⚠️ Câmera CSI conectada mas sem imagem')

    picam2.stop()
    picam2.close()

except Exception as e:
    print(f'❌ Câmera CSI falhou: {e}')
    print('💡 Verifique se a câmera está conectada corretamente')
"

# 6. Instalar outras dependências para QR codes
echo "📱 Instalando dependências para QR codes..."
pip install pyzbar Pillow --break-system-packages

# 7. Teste completo
echo "🎯 TESTE COMPLETO DO SISTEMA:"
echo "============================="

python3 -c "
# Teste importações
imports_ok = True

try:
    from picamera2 import Picamera2
    print('✅ picamera2')
except:
    print('❌ picamera2')
    imports_ok = False

try:
    import cv2
    print('✅ OpenCV')
except:
    print('❌ OpenCV')
    imports_ok = False

try:
    from pyzbar.pyzbar import decode
    print('✅ pyzbar')
except:
    print('❌ pyzbar')
    imports_ok = False

if imports_ok:
    print('')
    print('🎉 SISTEMA PRONTO!')
    print('==================')
    print('Agora você pode usar:')
    print('python qr_reader_simple.py --visual')
else:
    print('')
    print('❌ ALGUMAS DEPENDÊNCIAS FALHARAM')
    print('===============================')
    print('Execute: bash install_qr_simple.sh')
"

echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "==================="
echo "1. Reinicie o terminal/shell"
echo "2. Ative o ambiente virtual:"
echo "   source venv/bin/activate"
echo "3. Teste o sistema:"
echo "   python qr_reader_simple.py --visual"
echo ""
echo "💡 DICAS PARA CSI:"
echo "=================="
echo "- Câmeras chinesas CSI genéricas funcionam apenas com picamera2"
echo "- NÃO funcionam com OpenCV/V4L2"
echo "- Use resolução 1280x720 para melhor detecção de QR codes"