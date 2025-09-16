#!/bin/bash

# Script para instalar dependências essenciais do AGV no Raspberry Pi
# Execute como: bash install_deps.sh

echo "📦 INSTALADOR DE DEPENDÊNCIAS - Sistema AGV"
echo "=========================================="

# Verifica se está rodando como root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Não execute como root!"
   echo "Execute como usuário normal: bash install_deps.sh"
   exit 1
fi

echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    echo "Instale com: sudo apt install python3 python3-pip"
    exit 1
fi

echo "✅ Python3 encontrado"

# Instala dependências essenciais
echo ""
echo "📥 Instalando dependências Python..."

pip3 install --user flask flask-cors requests pyserial

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dependências instaladas com sucesso!"
    echo ""
    echo "🧪 Testando instalação..."
    python3 -c "import flask, flask_cors, requests, serial; print('✅ Todas as dependências OK!')"
    echo ""
    echo "🎯 PRÓXIMOS PASSOS:"
    echo "   1. Execute: python find_pc_ip.py"
    echo "   2. Execute: python next_steps.py"
    echo "   3. Teste os controles manuais na interface web"
else
    echo ""
    echo "❌ Erro na instalação!"
    echo "Tente instalar manualmente:"
    echo "   pip3 install --user flask flask-cors requests pyserial"
fi