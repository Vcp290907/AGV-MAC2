#!/bin/bash

# Script de instalação do AGV Raspberry Pi
# Execute como root: sudo bash install.sh

set -e

echo "🚀 Iniciando instalação do Sistema AGV - Raspberry Pi"
echo "=================================================="

# Verificar se está executando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script deve ser executado como root (sudo)"
    exit 1
fi

# Atualizar sistema
echo "📦 Atualizando sistema..."
apt update && apt upgrade -y

# Instalar dependências do sistema (compatível com Raspberry Pi OS Bookworm)
echo "🔧 Instalando dependências do sistema..."

# Atualizar lista de pacotes
apt update

# Instalar pacotes básicos
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    v4l-utils \
    build-essential \
    pkg-config

# Instalar bibliotecas básicas para OpenCV (compatível com Bookworm)
echo "📦 Instalando bibliotecas básicas para OpenCV..."
apt install -y \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    libhdf5-dev \
    libgtk2.0-dev

# Instalar Python packages
echo "🐍 Instalando pacotes Python..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p /var/log
mkdir -p /home/pi/agv_data
mkdir -p /home/pi/agv-raspberry

# Configurar permissões
echo "🔐 Configurando permissões..."
chown pi:pi /var/log/agv_system.log 2>/dev/null || touch /var/log/agv_system.log
chown pi:pi /home/pi/agv_data
chown pi:pi /home/pi/agv-raspberry

# Configurar GPIO (opcional)
echo "📌 Configurando GPIO..."
usermod -a -G gpio pi 2>/dev/null || true
usermod -a -G dialout pi  # Para acesso serial

# Configurar câmera (se existir)
echo "📷 Verificando câmera..."
if [ -e /dev/video0 ]; then
    echo "✅ Câmera detectada em /dev/video0"
    usermod -a -G video pi
else
    echo "⚠️  Nenhuma câmera detectada"
fi

# Configurar ESP32 (se conectado)
echo "🔌 Verificando ESP32..."
if [ -e /dev/ttyUSB0 ]; then
    echo "✅ ESP32 detectado em /dev/ttyUSB0"
else
    echo "⚠️  ESP32 não detectado (verifique conexão USB)"
fi

# Criar arquivo de configuração padrão
echo "⚙️  Criando configuração padrão..."
cat > /home/pi/agv_config.json << EOF
{
  "network": {
    "pc_ip": "192.168.0.100",
    "pc_port": 5000,
    "local_port": 8080,
    "auto_discovery": true
  },
  "hardware": {
    "camera": {
      "enabled": true,
      "device": 0,
      "resolution": [640, 480],
      "fps": 30
    },
    "esp32": {
      "enabled": true,
      "port": "/dev/ttyUSB0",
      "baudrate": 115200
    }
  },
  "system": {
    "log_level": "INFO",
    "log_file": "/var/log/agv_system.log",
    "data_directory": "/home/pi/agv_data"
  }
}
EOF

chown pi:pi /home/pi/agv_config.json

# Configurar inicialização automática (opcional)
echo "🔄 Configurando inicialização automática..."
read -p "Deseja configurar inicialização automática do AGV? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat >> /etc/rc.local << EOF

# Iniciar AGV System
su pi -c 'cd /home/pi/agv-raspberry && source venv/bin/activate && python main.py &' || true
EOF
    echo "✅ Inicialização automática configurada"
fi

# Verificar instalação
echo "🔍 Verificando instalação..."
python3 -c "import flask, cv2, serial; print('✅ Todas as dependências instaladas')"

echo ""
echo "🎉 Instalação concluída com sucesso!"
echo "==================================="
echo ""
echo "📋 Próximos passos:"
echo "1. Configure o IP do PC no arquivo config.py ou /home/pi/agv_config.json"
echo "2. Conecte a câmera USB (se não conectada)"
echo "3. Conecte o ESP32 via USB (se não conectado)"
echo "4. Execute: python main.py"
echo ""
echo "📖 Para mais informações, consulte o README.md"
echo ""
echo "🚀 Comando para iniciar: python main.py"
echo "📊 Monitorar logs: tail -f /var/log/agv_system.log"
echo "🛑 Parar sistema: curl -X POST http://localhost:8080/shutdown"