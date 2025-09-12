#!/bin/bash

# Script de instalação ULTRA SIMPLES do AGV Raspberry Pi
# Instala apenas o essencial, sem dependências problemáticas
# Execute como root: sudo bash install_ultra_simple.sh

set -e

echo "⚡ INSTALAÇÃO ULTRA SIMPLES - Sistema AGV Raspberry Pi"
echo "===================================================="

# Verificar se está executando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Execute como root: sudo bash install_ultra_simple.sh"
    exit 1
fi

# Apenas atualizar lista de pacotes (sem upgrade para evitar problemas)
echo "📦 Atualizando lista de pacotes..."
apt update

# Instalar apenas Python e ferramentas essenciais
echo "🐍 Instalando Python e ferramentas básicas..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    build-essential

# Criar estrutura de diretórios
echo "📁 Criando estrutura de diretórios..."
mkdir -p /home/vcp2909/agv-raspberry
mkdir -p /var/log
mkdir -p /home/vcp2909/agv_data

# Ajustar permissões
echo "🔐 Ajustando permissões..."
chown -R vcp2909:vcp2909 /home/vcp2909/agv-raspberry
chown -R vcp2909:vcp2909 /home/vcp2909/agv_data
touch /var/log/agv_system.log
chown vcp2909:vcp2909 /var/log/agv_system.log

# GPIO permissions
usermod -a -G gpio vcp2909 2>/dev/null || true
usermod -a -G dialout vcp2909

echo ""
echo "✅ Instalação ultra simples concluída!"
echo ""
echo "📋 MANUALMENTE, execute como usuário pi:"
echo ""
echo "1. Acesse como usuário pi:"
echo "   su - vcp2909"
echo ""
echo "2. Vá para o diretório:"
echo "   cd /home/vcp2909/agv-raspberry"
echo ""
echo "3. Instale python3-full (necessário para venv):"
echo "   sudo apt install -y python3-full"
echo ""
echo "4. Crie ambiente virtual:"
echo "   python3 -m venv venv"
echo ""
echo "5. Ative ambiente virtual:"
echo "   source venv/bin/activate"
echo ""
echo "6. Instale dependências essenciais:"
echo "   pip install Flask Flask-CORS requests pyserial"
echo ""
echo "7. OU use --break-system-packages (NÃO RECOMENDADO):"
echo "   pip install --break-system-packages Flask Flask-CORS requests pyserial"
echo ""
echo "6. Descubra o IP do PC automaticamente:"
echo "   python find_pc_ip.py"
echo "   # OU configure manualmente:"
echo "   nano config.py"
echo "   # Altere pc_ip para o IP do seu PC"
echo ""
echo "7. Teste comunicação:"
echo "   python test_connection.py"
echo ""
echo "8. Execute sistema:"
echo "   python main.py"
echo ""
echo "📦 DEPENDÊNCIAS ADICIONAIS (OPCIONAIS):"
echo "   pip install Pillow numpy  # Para imagens básicas"
echo "   pip install opencv-python # Para visão computacional (pode falhar)"
echo ""
echo "🖼️  CÂMERA (se usar):"
echo "   sudo apt install v4l-utils"
echo "   sudo usermod -a -G video pi"
echo ""
echo "🔌 ESP32 (se usar):"
echo "   sudo apt install python3-serial"
echo ""
echo "🚀 Comando para iniciar:"
echo "   cd /home/vcp2909/agv-raspberry && source venv/bin/activate && python main.py"
echo ""
echo "📊 Para monitorar:"
echo "   tail -f /var/log/agv_system.log"
echo ""
echo "🛑 Para parar:"
echo "   curl -X POST http://localhost:8080/shutdown"
echo ""
echo "✅ VANTAGENS desta instalação:"
echo "   - ✅ Funciona em qualquer versão do Raspberry Pi OS"
echo "   - ✅ Sem dependências problemáticas"
echo "   - ✅ Instalação rápida e confiável"
echo "   - ✅ Fácil de debugar se houver problemas"
echo "   - ✅ Pode adicionar recursos gradualmente"