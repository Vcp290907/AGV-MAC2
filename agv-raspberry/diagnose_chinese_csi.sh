#!/bin/bash

# 🔍 Diagnóstico Detalhado - Câmera CSI Chinesa
# Baseado nos resultados do teste: v4l2-ctl OK mas 0 bytes

echo "🔬 DIAGNÓSTICO DETALHADO - CÂMERA CSI CHINESA"
echo "=============================================="

# 1. Verificar conexão física
echo ""
echo "🔌 1. VERIFICANDO CONEXÃO FÍSICA..."
echo "=================================="

# Verificar se câmera está conectada via CSI
CSI_CONNECTED=$(vcgencmd get_camera 2>/dev/null | grep -o "detected=[0-1]" | cut -d'=' -f2)
if [ "$CSI_CONNECTED" = "1" ]; then
    echo "✅ CSI: Câmera oficial detectada (vcgencmd)"
else
    echo "⚠️  CSI: Nenhuma câmera oficial detectada (normal para chinesas)"
fi

# Verificar dispositivos V4L2
echo ""
echo "📹 2. VERIFICANDO DISPOSITIVOS V4L2..."
echo "===================================="
if command -v v4l2-ctl &> /dev/null; then
    echo "Dispositivos V4L2 encontrados:"
    v4l2-ctl --list-devices | head -20

    # Verificar especificamente /dev/video0
    if [ -e /dev/video0 ]; then
        echo ""
        echo "📷 /dev/video0 encontrado. Verificando capacidades:"
        v4l2-ctl --device=/dev/video0 --info 2>/dev/null || echo "   ❌ Erro ao obter info de /dev/video0"
    else
        echo "❌ /dev/video0 não encontrado"
    fi
else
    echo "❌ v4l2-ctl não instalado"
fi

# 2. Testar captura básica
echo ""
echo "📸 3. TESTANDO CAPTURA BÁSICA..."
echo "==============================="

# Teste com timeout menor e formato específico
echo "Testando v4l2-ctl com diferentes configurações..."

# Teste 1: YUYV (mais comum)
echo ""
echo "🧪 Teste 1: YUYV 640x480"
v4l2-ctl --device=/dev/video0 --set-fmt-video=width=640,height=480,pixelformat=YUYV --stream-mmap --stream-count=1 --stream-to=test1.raw 2>&1
if [ -f test1.raw ]; then
    SIZE1=$(stat -c%s test1.raw 2>/dev/null || echo "0")
    echo "   📁 Arquivo: ${SIZE1} bytes"
    rm -f test1.raw
else
    echo "   ❌ Arquivo não criado"
fi

# Teste 2: RGB
echo ""
echo "🧪 Teste 2: RGB3 320x240"
v4l2-ctl --device=/dev/video0 --set-fmt-video=width=320,height=240,pixelformat=RGB3 --stream-mmap --stream-count=1 --stream-to=test2.raw 2>&1
if [ -f test2.raw ]; then
    SIZE2=$(stat -c%s test2.raw 2>/dev/null || echo "0")
    echo "   📁 Arquivo: ${SIZE2} bytes"
    rm -f test2.raw
else
    echo "   ❌ Arquivo não criado"
fi

# 3. Verificar drivers e módulos
echo ""
echo "🔧 4. VERIFICANDO DRIVERS E MÓDULOS..."
echo "====================================="
echo "Módulos V4L2 carregados:"
lsmod | grep -E "(v4l|bcm|rp1)" || echo "   Nenhum módulo V4L2 encontrado"

echo ""
echo "Versão do kernel:"
uname -r

# 4. Verificar logs do sistema
echo ""
echo "📋 5. VERIFICANDO LOGS DO SISTEMA..."
echo "==================================="
echo "Logs relacionados à câmera (últimas 10 linhas):"
dmesg | grep -i -E "(camera|csi|video|v4l)" | tail -10 || echo "   Nenhum log de câmera encontrado"

# 5. Verificar alimentação e hardware
echo ""
echo "⚡ 6. VERIFICAÇÃO DE HARDWARE..."
echo "==============================="

# Verificar tensão (se disponível)
if command -v vcgencmd &> /dev/null; then
    echo "Temperatura da CPU: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
    echo "Voltagem da core: $(vcgencmd measure_volts core 2>/dev/null || echo 'N/A')"
fi

# Verificar se há processos usando a câmera
echo ""
echo "🔍 7. PROCESSOS USANDO CÂMERA..."
echo "==============================="
echo "Processos com câmera aberta:"
lsof /dev/video* 2>/dev/null || echo "   Nenhum processo usando dispositivos video"

echo ""
echo "🎯 DIAGNÓSTICO CONCLUÍDO"
echo "========================"
echo ""
echo "💡 INTERPRETAÇÃO DOS RESULTADOS:"
echo "=================================="

if [ -e /dev/video0 ]; then
    echo "✅ /dev/video0 existe - driver funcionando"
else
    echo "❌ /dev/video0 não existe - problema de driver"
fi

if [ "$SIZE1" -gt 0 ] 2>/dev/null; then
    echo "✅ Captura YUYV funcionou - câmera respondendo"
else
    echo "❌ Captura YUYV falhou - câmera não respondendo"
fi

echo ""
echo "🔧 PRÓXIMAS AÇÕES RECOMENDADAS:"
echo "==============================="

if [ ! -e /dev/video0 ]; then
    echo "1. ⚡ Verificar alimentação da câmera (5V externo necessário?)"
    echo "2. 🔌 Verificar conexão física do cabo CSI"
    echo "3. 🔄 Reiniciar sistema: sudo reboot"
elif [ "$SIZE1" -eq 0 ] 2>/dev/null; then
    echo "1. ⚡ Verificar se câmera precisa de alimentação externa (5V)"
    echo "2. 🔌 Testar com outra câmera CSI chinesa"
    echo "3. 📷 Verificar se câmera é compatível com Pi 5"
    echo "4. 🔧 Testar diferentes formatos/resoluções"
fi

echo ""
echo "🧪 TESTES ADICIONAIS:"
echo "===================="
echo "• python3 test_chinese_csi_camera.py (teste atual)"
echo "• Tente conectar alimentação externa 5V à câmera"
echo "• Teste com resolução menor: 320x240"