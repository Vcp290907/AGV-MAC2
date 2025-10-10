#!/bin/bash
# Script SIMPLIFICADO de instalação das dependências QR codes para Raspberry Pi
# Versão confiável que evita problemas de compilação
# Execute como: bash install_qr_deps_simple.sh

echo "📦 Instalação SIMPLIFICADA - QR Codes no Raspberry Pi"
echo "===================================================="

# Verificar se estamos no Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️ Este script é otimizado para Raspberry Pi"
    echo "🔄 Continuando instalação genérica..."
fi

# Atualizar lista de pacotes
echo "🔄 Atualizando lista de pacotes..."
sudo apt update

# Instalar TODAS as dependências do sistema primeiro
echo "📦 Instalando dependências do sistema..."
sudo apt install -y \
    python3-opencv \
    python3-pip \
    python3-numpy \
    python3-pillow \
    python3-picamera2 \
    libcap-dev \
    python3-prctl \
    build-essential \
    python3-dev

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🏗️ Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar pacotes Python (apenas os essenciais)
echo "🐍 Instalando bibliotecas Python..."
pip install --upgrade pip
pip install pyzbar numpy Pillow

# Tentar instalar opencv-python (pode falhar, mas temos o do apt)
pip install opencv-python || echo "⚠️ OpenCV via pip falhou, usando versão do apt (OK)"

# Testar imports básicos
echo ""
echo "🧪 Testando imports básicos..."
python3 -c "
import cv2
import numpy as np
from PIL import Image
import pyzbar
print('✅ Imports básicos OK')
"

# Testar picamera2 se no Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "📷 Testando Picamera2..."
    python3 -c "
try:
    import picamera2
    print('✅ Picamera2 OK')
except ImportError as e:
    print(f'⚠️ Picamera2 não disponível: {e}')
"
fi

echo ""
echo "✅ Instalação simplificada concluída!"
echo ""
echo "🧪 Para testar o sistema:"
echo "   python teste_qr_sistema.py     # Teste básico"
echo "   python teste_qr_raspberry.py   # Teste completo (RPi only)"
echo ""
echo "📚 Para usar em código:"
echo "   from qr_code_reader import QRCodeReader"
echo ""
echo "💡 Se houver problemas, use apenas os pacotes do apt:"
echo "   sudo apt install -y python3-picamera2 python3-opencv"