#!/bin/bash
# Script de instalação das dependências QR codes para Raspberry Pi
# Execute como: bash install_qr_deps.sh

echo "📦 Instalando dependências do sistema QR codes..."
echo "================================================="

# Verificar se estamos no Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️ Este script é otimizado para Raspberry Pi"
    echo "🔄 Continuando instalação genérica..."
fi

# Atualizar lista de pacotes
echo "🔄 Atualizando lista de pacotes..."
sudo apt update

# Instalar dependências do sistema
echo "📦 Instalando dependências do sistema..."
sudo apt install -y python3-opencv python3-pip python3-numpy

# Instalar bibliotecas Python
echo "🐍 Instalando bibliotecas Python..."

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🏗️ Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar pacotes Python
pip install --upgrade pip
pip install opencv-python pyzbar Pillow numpy

# Instalar picamera2 se no Raspberry Pi
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "📷 Instalando Picamera2 para câmera CSI..."
    sudo apt install -y python3-picamera2
    pip install picamera2
fi

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "🧪 Para testar o sistema:"
echo "   python teste_qr_sistema.py     # Teste básico"
echo "   python teste_qr_raspberry.py   # Teste completo (RPi only)"
echo ""
echo "📚 Para usar em código:"
echo "   from qr_code_reader import QRCodeReader"