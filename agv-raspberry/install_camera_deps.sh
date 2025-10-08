#!/bin/bash
"""
Script para instalar dependências de câmera no Raspberry Pi 5
Execute: bash install_camera_deps.sh
"""

echo "📦 INSTALANDO DEPENDÊNCIAS DE CÂMERA - RASPBERRY PI 5"
echo "======================================================"

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Não execute como root. Use: bash install_camera_deps.sh"
   exit 1
fi

echo "🔄 Atualizando sistema..."
sudo apt update

echo "📷 Instalando libcamera e ferramentas..."
sudo apt install -y python3-libcamera python3-kms++ libcamera-tools

echo "🎬 Instalando GStreamer para câmera..."
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libcamera

echo "🐍 Instalando bibliotecas Python..."
pip3 install opencv-python opencv-contrib-python numpy pillow

echo "🔧 Verificando instalação..."
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python3 -c "import numpy as np; print(f'NumPy: {np.__version__}')"

echo "✅ Instalação concluída!"
echo ""
echo "🧪 Execute os testes:"
echo "   python3 test_camera.py"
echo "   python3 test_csi_camera.py"
echo ""
echo "📚 Documentação:"
echo "   https://www.raspberrypi.com/documentation/computers/camera_software.html"