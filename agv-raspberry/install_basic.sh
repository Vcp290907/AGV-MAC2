#!/bin/bash

# Script de instalação básica do AGV Raspberry Pi
# Versão simplificada sem OpenCV para evitar problemas de dependências
# Execute como root: sudo bash install_basic.sh

set -e

echo "🚀 Iniciando instalação BÁSICA do Sistema AGV - Raspberry Pi"
echo "=========================================================="
echo "⚠️  NOTA: Esta versão NÃO inclui OpenCV para evitar problemas de dependências"
echo "📦 OpenCV pode ser instalado separadamente depois se necessário"
echo ""

# Verificar se está executando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script deve ser executado como root (sudo)"
    exit 1
fi

# Atualizar sistema
echo "📦 Atualizando sistema..."
apt update && apt upgrade -y

# Instalar dependências básicas do sistema
echo "🔧 Instalando dependências básicas..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    build-essential \
    pkg-config \
    libjpeg-dev \
    libpng-dev \
    libtiff5-dev

# Instalar bibliotecas básicas para imagens (simplificado)
echo "🖼️  Instalando bibliotecas básicas para imagens..."
apt install -y \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev

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

# Verificar câmera (opcional)
echo "📷 Verificando câmera..."
if [ -e /dev/video0 ]; then
    echo "✅ Câmera detectada em /dev/video0"
    apt install -y v4l-utils
    usermod -a -G video pi
else
    echo "⚠️  Nenhuma câmera detectada (instale uma câmera USB se necessário)"
fi

# Verificar ESP32 (opcional)
echo "🔌 Verificando ESP32..."
if [ -e /dev/ttyUSB0 ]; then
    echo "✅ ESP32 detectado em /dev/ttyUSB0"
else
    echo "⚠️  ESP32 não detectado (conecte via USB se necessário)"
fi

# Criar ambiente virtual e instalar pacotes básicos
echo "🐍 Criando ambiente virtual..."
su - pi -c "
cd /home/pi/agv-raspberry
python3 -m venv venv
source venv/bin/activate

echo '📦 Instalando pacotes Python básicos...'
pip install --upgrade pip

# Instalar pacotes essenciais primeiro
pip install Flask Flask-CORS requests pyserial Pillow numpy

echo '✅ Pacotes básicos instalados'
"

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
      "enabled": false,
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
echo "🔍 Verificando instalação básica..."
su - pi -c "
cd /home/pi/agv-raspberry
source venv/bin/activate
python3 -c 'import flask, requests, serial, PIL, numpy; print(\"✅ Dependências básicas OK\")'
"

echo ""
echo "🎉 Instalação BÁSICA concluída com sucesso!"
echo "==========================================="
echo ""
echo "📋 O que foi instalado:"
echo "✅ Python 3 e pip"
echo "✅ Flask e bibliotecas web"
echo "✅ Requests para HTTP"
echo "✅ PySerial para ESP32"
echo "✅ Pillow e NumPy para imagens"
echo "✅ Ambiente virtual configurado"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure o IP do PC no arquivo config.py ou /home/pi/agv_config.json"
echo "2. Teste a comunicação: python test_connection.py"
echo "3. Execute o sistema: python main.py"
echo ""
echo "📋 Para instalar OpenCV (opcional):"
echo "   sudo apt install python3-opencv"
echo "   # Ou use: pip install opencv-python (pode demorar)"
echo ""
echo "🚀 Comando para iniciar: cd /home/pi/agv-raspberry && source venv/bin/activate && python main.py"
echo "📊 Monitorar logs: tail -f /var/log/agv_system.log"
echo "🛑 Parar sistema: curl -X POST http://localhost:8080/shutdown"