#!/bin/bash
# filepath: setup_raspberry.sh

echo "========================================="
echo "    Configurando AGV System no Raspberry Pi"
echo "========================================="

# Atualizar sistema
echo "Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências do sistema
echo "Instalando dependências..."
sudo apt install -y python3-pip python3-venv nodejs npm git

# Criar ambiente virtual para o backend
echo "Configurando backend..."
cd agv-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Configurar frontend
echo "Configurando frontend..."
cd agv-frontend
npm install
npm run build
cd ..

echo "========================================="
echo "    Setup concluído!"
echo "    Backend: source agv-backend/venv/bin/activate && python agv-backend/app.py"
echo "    Frontend: serve -s agv-frontend/build"
echo "========================================="