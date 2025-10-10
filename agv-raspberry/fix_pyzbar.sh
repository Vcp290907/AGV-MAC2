#!/bin/bash
# Correção rápida para instalar pyzbar no ambiente virtual
# Execute como: bash fix_pyzbar.sh

echo "🔧 Corrigindo instalação do pyzbar..."
echo "====================================="

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

# Verificar instalação
echo "🧪 Testando import..."
python3 -c "
try:
    from pyzbar.pyzbar import decode
    print('✅ pyzbar instalado com sucesso!')
except ImportError as e:
    print(f'❌ Erro no import: {e}')
"

echo ""
echo "✅ Correção concluída!"
echo "🧪 Teste o qr_code_reader.py agora"