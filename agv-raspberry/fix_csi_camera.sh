#!/bin/bash
"""
Script de correção automática para câmera CSI no Raspberry Pi 5
Execute: bash fix_csi_camera.sh
"""

echo "🔧 CORREÇÃO AUTOMÁTICA - CÂMERA CSI RASPBERRY PI 5"
echo "=================================================="

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Não execute como root. Use: bash fix_csi_camera.sh"
   exit 1
fi

echo "⚠️  Este script fará alterações no sistema."
echo "Pressione Enter para continuar ou Ctrl+C para cancelar..."
read

echo ""
echo "1️⃣ ATUALIZANDO SISTEMA..."
echo "========================="
sudo apt update
sudo apt upgrade -y

echo ""
echo "2️⃣ INSTALANDO DEPENDÊNCIAS DA CÂMERA..."
echo "======================================"
sudo apt install -y python3-libcamera python3-kms++ libcamera-tools
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libcamera
sudo apt install -y v4l-utils

echo ""
echo "3️⃣ INSTALANDO BIBLIOTECAS PYTHON..."
echo "=================================="
pip3 install opencv-python opencv-contrib-python numpy pillow pyzbar qrcode[pil]

echo ""
echo "4️⃣ CONFIGURANDO CÂMERA NO SISTEMA..."
echo "==================================="

# Verificar e adicionar configuração da câmera
CONFIG_FILE="/boot/firmware/config.txt"
if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "camera_auto_detect" "$CONFIG_FILE"; then
        echo "📝 Adicionando camera_auto_detect=1 ao config.txt..."
        echo "camera_auto_detect=1" | sudo tee -a "$CONFIG_FILE"
    else
        echo "✅ camera_auto_detect já configurado"
    fi
else
    echo "❌ Arquivo $CONFIG_FILE não encontrado"
fi

echo ""
echo "5️⃣ CONFIGURANDO PERMISSÕES..."
echo "============================="

# Adicionar usuário ao grupo video
if ! groups $USER | grep -q video; then
    echo "👤 Adicionando usuário ao grupo video..."
    sudo usermod -a -G video $USER
    echo "✅ Usuário adicionado ao grupo video"
    echo "⚠️  Será necessário fazer logout/login ou reboot"
else
    echo "✅ Usuário já está no grupo video"
fi

echo ""
echo "6️⃣ HABILITANDO CÂMERA VIA raspi-config..."
echo "========================================="

# Tentar automatizar o raspi-config (limitado)
echo "⚠️  Não é possível automatizar raspi-config completamente"
echo "📋 Execute manualmente:"
echo "   sudo raspi-config"
echo "   → Interfacing Options"
echo "   → Camera"
echo "   → Enable"
echo "   → Finish"
echo "   → Reboot"

echo ""
echo "7️⃣ TESTANDO INSTALAÇÃO..."
echo "========================="

# Testar libcamera
echo "🧪 Testando libcamera..."
if command -v libcamera-hello &> /dev/null; then
    echo "✅ libcamera instalado"
else
    echo "❌ libcamera falhou"
fi

# Testar OpenCV
echo "🧪 Testando OpenCV..."
python3 -c "
try:
    import cv2
    print('✅ OpenCV instalado - versão:', cv2.__version__)
except ImportError:
    print('❌ OpenCV falhou')
" 2>/dev/null

echo ""
echo "8️⃣ VERIFICAÇÃO FINAL..."
echo "======================"

echo "🔍 Verificando detecção da câmera..."
vcgencmd get_camera

echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "=================="
echo ""
echo "1. ✅ Execute: sudo raspi-config (habilitar câmera)"
echo "2. 🔄 Reinicie: sudo reboot"
echo "3. 🧪 Teste: python3 test_csi_camera.py"
echo "4. 📊 Diagnóstico: bash diagnose_csi_camera.sh"
echo ""
echo "💡 Se ainda não funcionar:"
echo "- Verifique conexão física do cabo flat"
echo "- Teste com outra câmera CSI"
echo "- Consulte documentação oficial"

echo ""
echo "🎉 CORREÇÃO AUTOMÁTICA CONCLUÍDA!"
echo "Reinicie o sistema e teste novamente."