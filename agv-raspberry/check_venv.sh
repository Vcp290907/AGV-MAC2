#!/bin/bash
# Script para verificar e corrigir o ambiente virtual
# Execute como: bash check_venv.sh

echo "🔍 Verificando ambiente virtual..."
echo "================================="

# Verificar se estamos no diretório correto
if [ ! -f "qr_code_reader.py" ]; then
    echo "❌ Arquivo qr_code_reader.py não encontrado!"
    echo "📂 Execute este script do diretório agv-raspberry/"
    exit 1
fi

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "🏗️ Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🐍 Ativando ambiente virtual..."
source venv/bin/activate

# Verificar se está ativado
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ Ambiente virtual ativado: $VIRTUAL_ENV"
else
    echo "❌ Falha ao ativar ambiente virtual"
    exit 1
fi

# Verificar Python
PYTHON_VERSION=$(python3 --version)
echo "✅ Python: $PYTHON_VERSION"

# Verificar pacotes
echo ""
echo "📦 Verificando pacotes instalados..."

check_package() {
    local package=$1
    local test_cmd=$2
    echo -n "🔍 $package... "
    if python3 -c "$test_cmd" 2>/dev/null; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FALHA"
        return 1
    fi
}

check_package "pyzbar" "from pyzbar.pyzbar import decode; print('OK')"
check_package "OpenCV" "import cv2; print(cv2.__version__)"
check_package "NumPy" "import numpy as np; print('OK')"
check_package "Pillow" "from PIL import Image; print('OK')"

# Verificar picamera2 se no Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    check_package "picamera2" "import picamera2; print('OK')"
    check_package "libcamera" "import libcamera; print('OK')"
fi

echo ""
echo "🎯 Para usar o ambiente virtual:"
echo "   source venv/bin/activate"
echo "   python3 seu_script.py"
echo ""
echo "💡 Ou use o wrapper:"
echo "   ./run_python.sh seu_script.py"

echo ""
echo "✅ Verificação concluída!"