#!/bin/bash

# Instalação RÁPIDA do AGV Raspberry Pi
# Copia arquivos e instala apenas o essencial
# Execute como root: sudo bash quick_start.sh

set -e

echo "⚡ INSTALAÇÃO RÁPIDA - Sistema AGV Raspberry Pi"
echo "=============================================="

# Verificar se está executando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Execute como root: sudo bash quick_start.sh"
    exit 1
fi

# Instalar apenas o essencial
echo "📦 Instalando Python e ferramentas básicas..."
apt update
apt install -y python3 python3-pip python3-venv git

# Criar estrutura de diretórios
echo "📁 Criando diretórios..."
mkdir -p /home/pi/agv-raspberry
mkdir -p /var/log
mkdir -p /home/pi/agv_data

# Ajustar permissões
echo "🔐 Ajustando permissões..."
chown -R pi:pi /home/pi/agv-raspberry
chown -R pi:pi /home/pi/agv_data
touch /var/log/agv_system.log
chown pi:pi /var/log/agv_system.log

# GPIO permissions
usermod -a -G gpio pi 2>/dev/null || true
usermod -a -G dialout pi

echo ""
echo "✅ Instalação básica concluída!"
echo ""
echo "📋 PRÓXIMOS PASSOS MANUAIS:"
echo ""
echo "1. Acesse como usuário pi:"
echo "   su - pi"
echo ""
echo "2. Vá para o diretório:"
echo "   cd /home/pi/agv-raspberry"
echo ""
echo "3. Crie ambiente virtual:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "4. Instale dependências:"
echo "   pip install Flask Flask-CORS requests pyserial Pillow numpy"
echo ""
echo "5. Configure o IP do PC em config.py:"
echo "   nano config.py"
echo ""
echo "6. Execute o sistema:"
echo "   python main.py"
echo ""
echo "📊 Para monitorar:"
echo "   tail -f /var/log/agv_system.log"
echo ""
echo "🛑 Para parar:"
echo "   curl -X POST http://localhost:8080/shutdown"
echo ""
echo "🎯 Teste de conectividade:"
echo "   python test_connection.py"
echo ""
echo "💡 DICA: Se tiver problemas com OpenCV, use a instalação básica"
echo "   sem instalar opencv-python por enquanto."