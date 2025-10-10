#!/bin/bash
# Script para reinstalar pyzbar e suas dependências
# Execute como: bash reinstall_pyzbar.sh

echo "🔄 Reinstalando pyzbar completamente..."
echo "======================================"

# Verificar se estamos no Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️ Este script é otimizado para Raspberry Pi"
    echo "🔄 Continuando instalação genérica..."
fi

# Instalar dependências do sistema para zbar/pyzbar
echo "📦 Instalando dependências do sistema..."
sudo apt update
sudo apt install -y \
    libzbar0 \
    libzbar-dev \
    python3-dev \
    build-essential \
    pkg-config

# Ativar ambiente virtual
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "🏗️ Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Desinstalar pyzbar se existir
echo "🗑️ Removendo pyzbar antigo..."
pip uninstall pyzbar -y 2>/dev/null || echo "pyzbar não estava instalado"

# Limpar cache pip
echo "🧹 Limpando cache..."
pip cache purge

# Instalar pyzbar limpo
echo "📦 Instalando pyzbar..."
pip install --no-cache-dir pyzbar

# Verificar instalação
echo "🧪 Testando pyzbar..."
python3 -c "
try:
    from pyzbar.pyzbar import decode
    import numpy as np
    # Teste básico
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    result = decode(test_image)
    print('✅ pyzbar instalado e funcionando!')
except ImportError as e:
    print(f'❌ Erro no import: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️ pyzbar importado mas erro no teste: {e}')
"

echo ""
echo "✅ Reinstalação concluída!"
echo ""
echo "🧪 Teste com: python qr_code_reader.py"