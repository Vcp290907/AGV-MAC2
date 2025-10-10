#!/bin/bash
# Script de inicialização do sistema AGV
# Execute como: bash start_agv.sh [opção]

echo "🚀 SISTEMA AGV - Inicialização"
echo "=============================="

# Verificar se estamos no diretório correto
if [ ! -f "main.py" ]; then
    echo "❌ Arquivo main.py não encontrado!"
    echo "📂 Execute este script do diretório agv-raspberry/"
    exit 1
fi

# Verificar se estamos no Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "✅ Executando no Raspberry Pi"
    IS_RPI=true
else
    echo "⚠️ Executando em ambiente não-Raspberry Pi (desenvolvimento)"
    IS_RPI=false
fi

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar dependências básicas
echo "🧪 Verificando dependências..."
python3 -c "
import sys
try:
    import asyncio
    import logging
    print('✅ Dependências básicas OK')
except ImportError as e:
    print(f'❌ Dependência faltando: {e}')
    sys.exit(1)
"

# Opções de execução
case "${1:-normal}" in
    "normal")
        echo ""
        echo "▶️ MODO NORMAL: Sistema AGV completo"
        echo "======================================"
        echo "🛑 Para parar: Ctrl+C"
        echo ""
        if [ "$IS_RPI" = true ]; then
            echo "⚠️ IMPORTANTE: Execute como root para acesso completo ao hardware"
            echo "   sudo bash start_agv.sh normal"
            echo ""
        fi
        python3 main.py
        ;;

    "background")
        echo ""
        echo "▶️ MODO BACKGROUND: Sistema em segundo plano"
        echo "============================================"
        echo "📊 Para ver logs: tail -f /var/log/agv_system.log"
        echo "🛑 Para parar: pkill -f main.py"
        echo ""
        nohup python3 main.py > /dev/null 2>&1 &
        echo "✅ Sistema iniciado em background (PID: $!)"
        ;;

    "debug")
        echo ""
        echo "▶️ MODO DEBUG: Sistema com logs detalhados"
        echo "==========================================="
        echo "🛑 Para parar: Ctrl+C"
        echo ""
        export PYTHONPATH="$PWD:$PYTHONPATH"
        python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import main
import asyncio
asyncio.run(main.main())
"
        ;;

    "test")
        echo ""
        echo "🧪 MODO TESTE: Verificação de componentes"
        echo "========================================="
        echo "Executando testes básicos..."
        echo ""

        # Teste de imports
        python3 -c "
try:
    from agv_camera import AGVCamera
    print('✅ AGVCamera importado')
except ImportError as e:
    print(f'⚠️ AGVCamera não disponível: {e}')
"

        # Teste de QR codes
        if [ -f "teste_qr_sistema.py" ]; then
            python3 teste_qr_sistema.py
        fi

        # Teste de comunicação
        if [ -f "test_connection.py" ]; then
            python3 test_connection.py
        fi
        ;;

    "status")
        echo ""
        echo "📊 STATUS DO SISTEMA"
        echo "===================="

        # Verificar se está rodando
        if pgrep -f "main.py" > /dev/null; then
            echo "✅ Sistema AGV está rodando"
            ps aux | grep "main.py" | grep -v grep
        else
            echo "❌ Sistema AGV não está rodando"
        fi

        echo ""
        echo "📝 Logs recentes:"
        if [ -f "/var/log/agv_system.log" ]; then
            tail -10 /var/log/agv_system.log
        else
            echo "Nenhum log encontrado em /var/log/agv_system.log"
        fi
        ;;

    "stop")
        echo ""
        echo "🛑 PARANDO SISTEMA AGV"
        echo "======================="
        pkill -f "main.py"
        echo "✅ Sistema parado"
        ;;

    *)
        echo ""
        echo "❓ OPÇÕES DISPONÍVEIS:"
        echo "======================"
        echo "  normal     - Executar sistema completo (padrão)"
        echo "  background - Executar em segundo plano"
        echo "  debug      - Executar com logs detalhados"
        echo "  test       - Executar testes de componentes"
        echo "  status     - Verificar status do sistema"
        echo "  stop       - Parar sistema em execução"
        echo ""
        echo "📝 Exemplos:"
        echo "  bash start_agv.sh normal"
        echo "  bash start_agv.sh background"
        echo "  bash start_agv.sh test"
        ;;
esac