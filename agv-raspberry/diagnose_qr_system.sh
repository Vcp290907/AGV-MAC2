#!/bin/bash
# Script completo de diagnóstico e correção do sistema QR codes
# Execute como: bash diagnose_qr_system.sh

echo "🔍 DIAGNÓSTICO COMPLETO - Sistema QR Codes"
echo "==========================================="

# Verificar se estamos no Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "✅ Executando no Raspberry Pi"
    IS_RPI=true
else
    echo "⚠️ Executando em ambiente não-Raspberry Pi"
    IS_RPI=false
fi

# Verificar se estamos no diretório correto
if [ ! -f "qr_code_reader.py" ]; then
    echo "❌ Arquivo qr_code_reader.py não encontrado!"
    echo "📂 Execute este script do diretório agv-raspberry/"
    exit 1
fi

echo ""
echo "1️⃣ VERIFICANDO DEPENDÊNCIAS DO SISTEMA..."
echo "=========================================="

# Verificar bibliotecas C/C++
check_system_dep() {
    local dep=$1
    local package=$2
    if dpkg -l | grep -q "^ii  $package"; then
        echo "✅ $dep instalado"
        return 0
    else
        echo "❌ $dep FALTANDO - instalar com: sudo apt install -y $package"
        return 1
    fi
}

check_system_dep "libzbar0" "libzbar0"
check_system_dep "libzbar-dev" "libzbar-dev"
check_system_dep "python3-picamera2" "python3-picamera2"
check_system_dep "python3-libcamera" "python3-libcamera"

echo ""
echo "2️⃣ VERIFICANDO AMBIENTE VIRTUAL..."
echo "==================================="

# Verificar ambiente virtual
if [ -d "venv" ]; then
    echo "✅ Ambiente virtual encontrado"

    # Ativar ambiente virtual
    source venv/bin/activate
    echo "✅ Ambiente virtual ativado"

    # Verificar Python no venv
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Ambiente virtual não encontrado"
    echo "🏗️ Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Ambiente virtual criado e ativado"
fi

echo ""
echo "3️⃣ VERIFICANDO PACOTES PYTHON..."
echo "================================="

# Função para verificar pacote Python
check_python_dep() {
    local package=$1
    local test_code=$2

    echo -n "🔍 Testando $package... "
    if python3 -c "$test_code" 2>/dev/null; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FALHA"
        return 1
    fi
}

# Testes dos pacotes
check_python_dep "OpenCV" "import cv2; print(cv2.__version__)"
check_python_dep "NumPy" "import numpy as np; print(np.__version__)"
check_python_dep "Pillow" "from PIL import Image; print('OK')"
check_python_dep "pyzbar" "from pyzbar.pyzbar import decode; print('OK')"

if [ "$IS_RPI" = true ]; then
    check_python_dep "picamera2" "import picamera2; print('OK')"
    check_python_dep "libcamera" "import libcamera; print('OK')"
fi

echo ""
echo "4️⃣ TESTANDO SISTEMA QR CODES..."
echo "==============================="

# Teste do qr_code_reader.py
echo -n "🔍 Testando qr_code_reader.py... "
if python3 -c "
try:
    from qr_code_reader import QRCodeReader
    reader = QRCodeReader(camera_id=0)
    print('Classe criada com sucesso')
    print('✅ qr_code_reader.py OK')
except Exception as e:
    print(f'❌ ERRO: {e}')
    exit 1
"; then
    echo "✅ Sistema QR codes funcional!"
else
    echo "❌ Sistema QR codes com problemas"
fi

echo ""
echo "5️⃣ RECOMENDAÇÕES..."
echo "==================="

echo "📋 Para corrigir problemas encontrados:"
echo ""
echo "🔧 Para pyzbar:"
echo "   bash reinstall_pyzbar.sh"
echo ""
echo "🔧 Para dependências gerais:"
echo "   bash fix_python_deps.sh"
echo ""
echo "🔧 Para instalar tudo:"
echo "   bash install_qr_deps_simple.sh"
echo ""
echo "🧪 Para testar:"
echo "   source venv/bin/activate"
echo "   python qr_code_reader.py"
echo ""
echo "🚀 Para executar AGV:"
echo "   sudo bash start_agv.sh normal"

echo ""
echo "✅ Diagnóstico concluído!"