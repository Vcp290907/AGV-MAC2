#!/bin/bash
# Script de correção para erro do libcap no picamera2
# Execute como: bash fix_libcap_error.sh

echo "🔧 Corrigindo erro do libcap para picamera2..."
echo "=============================================="

# Instalar dependências necessárias
echo "📦 Instalando headers do libcap..."
sudo apt update
sudo apt install -y libcap-dev python3-prctl build-essential python3-dev

# Tentar instalar picamera2 novamente
echo "📷 Instalando picamera2..."
pip install picamera2

# Verificar se funcionou
echo "🧪 Testando import..."
python3 -c "
try:
    import picamera2
    print('✅ Picamera2 instalado com sucesso!')
except ImportError as e:
    print(f'❌ Ainda há problemas: {e}')
"

echo ""
echo "✅ Correção aplicada!"
echo "🧪 Teste o sistema com: python teste_qr_raspberry.py"