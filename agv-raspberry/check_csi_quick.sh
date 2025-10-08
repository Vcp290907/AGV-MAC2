#!/bin/bash

# 🚀 Verificação Rápida de Câmera CSI
# Script simples para verificar o estado básico da câmera antes dos testes completos

echo "🔍 VERIFICAÇÃO RÁPIDA - CÂMERA CSI"
echo "=================================="

# Verificar detecção da câmera
echo ""
echo "📷 Verificando detecção da câmera..."
CAMERA_DETECT=$(vcgencmd get_camera 2>/dev/null | grep -o "detected=[0-1]" | cut -d'=' -f2)

if [ "$CAMERA_DETECT" = "1" ]; then
    echo "✅ Câmera detectada (detected=1)"
else
    echo "❌ Câmera NÃO detectada (detected=0)"
    echo "   💡 Verifique a conexão física do cabo flat CSI"
fi

# Verificar libcamera
echo ""
echo "🔧 Verificando libcamera..."
if command -v libcamera-hello &> /dev/null; then
    echo "✅ libcamera instalado"
else
    echo "❌ libcamera NÃO encontrado"
    echo "   💡 Execute: bash install_camera_deps.sh"
fi

# Verificar grupo video
echo ""
echo "👤 Verificando permissões..."
if groups $USER | grep -q video; then
    echo "✅ Usuário no grupo 'video'"
else
    echo "❌ Usuário NÃO está no grupo 'video'"
    echo "   💡 Execute: sudo usermod -a -G video \$USER && sudo reboot"
fi

# Verificar configuração
echo ""
echo "⚙️  Verificando configuração..."
if grep -q "camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "✅ Câmera habilitada em config.txt"
else
    echo "❌ Câmera NÃO habilitada em config.txt"
    echo "   💡 Execute: sudo raspi-config (Interfacing Options -> Camera)"
fi

echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "=================="

if [ "$CAMERA_DETECT" != "1" ]; then
    echo "1. 🔌 Verifique conexão física do cabo CSI"
    echo "2. 📷 Teste com outra câmera se possível"
else
    echo "1. ✅ Detecção OK - câmera conectada"
fi

if ! command -v libcamera-hello &> /dev/null; then
    echo "2. 📦 Instale dependências: bash install_camera_deps.sh"
else
    echo "2. ✅ libcamera OK"
fi

if ! groups $USER | grep -q video; then
    echo "3. 👥 Adicione ao grupo video e reinicie"
else
    echo "3. ✅ Permissões OK"
fi

if ! grep -q "camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "4. ⚙️  Habilite câmera via raspi-config e reinicie"
else
    echo "4. ✅ Configuração OK"
fi

echo ""
echo "🧪 Execute teste completo: python3 test_csi_camera.py"
echo "🔧 Para diagnóstico detalhado: bash diagnose_csi_camera.sh"
echo "🛠️  Para correção automática: bash fix_csi_camera.sh"