#!/bin/bash

# 🔍 Teste Rápido de Conectividade CSI
# Verifica se há sinal no barramento CSI

echo "🔍 TESTE RÁPIDO DE CONECTIVIDADE CSI"
echo "===================================="

echo ""
echo "📋 VERIFICANDO STATUS ATUAL..."
echo "=============================="

# Verificar se dispositivo existe
if [ -e /dev/video0 ]; then
    echo "✅ /dev/video0 existe"
else
    echo "❌ /dev/video0 não existe"
    echo "   💡 Driver CSI não carregado"
    exit 1
fi

# Verificar logs recentes de CSI
echo ""
echo "📜 ÚLTIMOS LOGS CSI (10 segundos)..."
echo "==================================="
timeout 10 dmesg -w | grep -i csi | head -5 || echo "   Nenhum log CSI recente"

echo ""
echo "🧪 TESTE DE DETECÇÃO DE CÂMERA..."
echo "================================"

# Tentar detectar câmera por 5 segundos
echo "Aguardando detecção de câmera por 5 segundos..."
timeout 5 dmesg -w | grep -q "csi2_ch0 node link is enabled" && echo "✅ Câmera detectada!" || echo "❌ Nenhuma câmera detectada"

echo ""
echo "⚡ VERIFICAÇÃO DE ALIMENTAÇÃO..."
echo "==============================="

# Verificar se há processos usando CSI
CSI_PROCESSES=$(lsof /dev/video0 2>/dev/null | wc -l)
if [ "$CSI_PROCESSES" -gt 0 ]; then
    echo "⚠️  /dev/video0 está sendo usado por processos"
    lsof /dev/video0
else
    echo "✅ /dev/video0 livre para uso"
fi

echo ""
echo "🎯 DIAGNÓSTICO RÁPIDO:"
echo "====================="

# Verificar se há câmera conectada baseada nos logs
if dmesg | grep -q "csi2_ch0 node link is enabled"; then
    echo "✅ CÂMERA DETECTADA - Hardware OK"
    echo "💡 Execute: python3 test_chinese_csi_camera.py"
elif dmesg | tail -20 | grep -q "csi2_ch0 node link is not enabled"; then
    echo "❌ CÂMERA NÃO DETECTADA"
    echo ""
    echo "🔧 POSSÍVEIS CAUSAS:"
    echo "   1. Cabo CSI desconectado ou danificado"
    echo "   2. Câmera sem alimentação (conecte 5V externo)"
    echo "   3. Câmera danificada"
    echo "   4. Conector CSI do Pi 5 com problema"
    echo ""
    echo "🛠️  SOLUÇÕES:"
    echo "   • Verifique conexão física do cabo CSI"
    echo "   • Conecte alimentação 5V à câmera (se necessário)"
    echo "   • Teste com outra câmera CSI"
    echo "   • Execute: bash diagnose_chinese_csi.sh"
else
    echo "❓ Status indeterminado - execute diagnóstico completo"
fi