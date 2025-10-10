#!/bin/bash
# Script para corrigir conflito entre picamera2 do pip e do apt
# Execute como: bash fix_picamera2_conflict.sh

echo "🔧 Corrigindo conflito do picamera2..."
echo "====================================="

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Ambiente virtual não encontrado!"
    exit 1
fi

# Remover picamera2 do ambiente virtual (se existir)
echo "🗑️ Removendo picamera2 do ambiente virtual..."
pip uninstall picamera2 -y 2>/dev/null || echo "picamera2 não estava instalado no venv"

# Verificar se picamera2 do sistema está disponível
echo "🧪 Testando picamera2 do sistema..."
if python3 -c "
try:
    import picamera2
    print('✅ picamera2 do sistema OK')
    print(f'   Localização: {picamera2.__file__}')
except ImportError as e:
    print(f'❌ picamera2 não encontrado: {e}')
    echo '💡 Instale com: sudo apt install -y python3-picamera2'
    exit 1
"

# Testar libcamera
echo "🧪 Testando libcamera..."
if python3 -c "
try:
    import libcamera
    print('✅ libcamera OK')
except ImportError as e:
    print(f'⚠️ libcamera não encontrado: {e}')
    echo '💡 Isso é normal se estiver usando apenas picamera2 do apt'
"

echo ""
echo "✅ Conflito corrigido!"
echo ""
echo "🧪 Teste com: python qr_code_reader.py"