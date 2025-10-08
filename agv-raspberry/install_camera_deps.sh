#!/bin/bash
"""
Script para instalar dependências de câmera no Raspberry Pi 5
Execute: bash install_camera_deps.sh
"""

echo "📦 INSTALANDO DEPENDÊNCIAS DE CÂMERA CSI - RASPBERRY PI 5"
echo "========================================================"

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Não execute como root. Use: bash install_camera_deps.sh"
   exit 1
fi

echo "🔄 Atualizando sistema..."
sudo apt update

echo "� Instalando libcamera (essencial para CSI)..."
sudo apt install -y python3-libcamera python3-kms++ libcamera-tools

echo "📹 Instalando ferramentas V4L2 (essencial para câmeras chinesas CSI)..."
sudo apt install -y v4l-utils

echo "🐍 Instalando bibliotecas Python..."
pip3 install opencv-python opencv-contrib-python numpy pillow

echo "� Instalando suporte para QR codes..."
pip3 install pyzbar qrcode[pil]

echo "�🔧 Verificando instalação..."
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python3 -c "import numpy as np; print(f'NumPy: {np.__version__}')"

echo "✅ Instalação concluída!"
echo ""
echo "🧪 Execute os testes CSI:"
echo "   python3 test_csi_camera.py"
echo ""
echo "📚 Documentação:"
echo "   https://www.raspberrypi.com/documentation/computers/camera_software.html"