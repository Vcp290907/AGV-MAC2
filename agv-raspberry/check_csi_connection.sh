#!/bin/bash
"""
Script para verificar conexão e configuração da câmera CSI
Execute: bash check_csi_connection.sh
"""

echo "🔍 VERIFICANDO CONEXÃO DA CÂMERA CSI"
echo "====================================="

echo "1️⃣ Verificando detecção da câmera..."
vcgencmd get_camera

echo ""
echo "2️⃣ Verificando dispositivos de vídeo..."
ls -la /dev/video*

echo ""
echo "3️⃣ Verificando módulos do kernel carregados..."
lsmod | grep -E "(bcm2835|v4l2|videodev)"

echo ""
echo "4️⃣ Verificando configuração do raspi-config..."
if grep -q "camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "✅ Camera auto-detect habilitada em config.txt"
elif grep -q "start_x=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "✅ Camera start_x=1 encontrada em config.txt"
else
    echo "⚠️  Configuração da câmera não encontrada em config.txt"
    echo "   Execute: sudo raspi-config -> Interfacing Options -> Camera -> Enable"
fi

echo ""
echo "5️⃣ Testando libcamera (teste rápido)..."
if command -v libcamera-hello &> /dev/null; then
    echo "   Executando teste de 2 segundos..."
    timeout 3 libcamera-hello -t 2000 --qt-preview 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ libcamera funcionando!"
    else
        echo "❌ Erro no libcamera"
    fi
else
    echo "❌ libcamera não instalado"
fi

echo ""
echo "6️⃣ Verificando permissões..."
if groups $USER | grep -q video; then
    echo "✅ Usuário no grupo 'video'"
else
    echo "❌ Usuário NÃO está no grupo 'video'"
    echo "   Execute: sudo usermod -a -G video $USER"
    echo "   Depois faça logout/login ou reboot"
fi

echo ""
echo "7️⃣ Verificando logs do sistema..."
echo "Últimas mensagens relacionadas à câmera:"
dmesg | grep -i camera | tail -5

echo ""
echo "📋 RESUMO DA VERIFICAÇÃO"
echo "========================"

# Verificar camera detectada
if vcgencmd get_camera | grep -q "detected=1"; then
    echo "✅ Câmera CSI detectada"
else
    echo "❌ Câmera CSI NÃO detectada"
fi

# Verificar libcamera
if command -v libcamera-hello &> /dev/null; then
    echo "✅ libcamera instalado"
else
    echo "❌ libcamera NÃO instalado"
fi

# Verificar grupo video
if groups $USER | grep -q video; then
    echo "✅ Permissões corretas"
else
    echo "❌ Problema de permissões"
fi

echo ""
echo "💡 PRÓXIMOS PASSOS:"
echo "1. Se câmera não detectada: verifique conexão do cabo flat"
echo "2. Execute: sudo raspi-config -> habilitar câmera"
echo "3. Reinicie o Raspberry Pi: sudo reboot"
echo "4. Execute: bash install_camera_deps.sh"
echo "5. Teste: python3 test_csi_camera.py"