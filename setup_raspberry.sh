echo "========================================="
echo "    Configurando AGV System no Raspberry Pi"
echo "========================================="

sudo apt update && sudo apt upgrade -y

echo "Instalando dependências"
sudo apt install -y python3-pip python3-venv nodejs npm git

echo "Configurando backend..."
cd agv-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo "Configurando frontend..."
cd agv-frontend
npm install
npm run build
cd ..

echo "========================================="
echo "    Backend: source agv-backend/venv/bin/activate && python agv-backend/app.py"
echo "    Frontend: serve -s agv-frontend/build"
echo "========================================="