#!/bin/bash
# Correção completa das dependências Python (pyzbar + picamera2)
# Execute como: bash fix_python_deps.sh

echo "🔧 Corrigindo dependências Python (pyzbar + picamera2)..."
echo "========================================================"

# Verificar se estamos no diretório correto
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "🏗️ Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🐍 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar pyzbar no ambiente virtual
echo "📦 Instalando pyzbar..."
pip install pyzbar

# Instalar picamera2 se no Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "📷 Instalando dependências do sistema para câmera..."
    sudo apt install -y python3-libcamera python3-picamera2 libcamera-dev

    echo "📷 Testando picamera2 do apt (mais confiável)..."
    # A versão do apt já vem com libcamera integrado
fi

# Verificar instalação
echo "🧪 Testando imports..."
python3 -c "
try:
    from pyzbar.pyzbar import decode
    print('✅ pyzbar OK')
except ImportError as e:
    print(f'❌ pyzbar erro: {e}')
"

if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    python3 -c "
try:
        import picamera2
        print('✅ picamera2 OK')
    except ImportError as e:
        print(f'⚠️ picamera2 erro: {e}')
    "
    python3 -c "
try:
        import libcamera
        print('✅ libcamera OK')
    except ImportError as e:
        print(f'⚠️ libcamera erro: {e}')
    "
fi

echo ""
echo "✅ Correção concluída!"
echo "🧪 Teste o qr_code_reader.py agora"