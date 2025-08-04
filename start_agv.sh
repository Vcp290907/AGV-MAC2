#!/bin/bash
# filepath: c:\Users\VCP2909\Desktop\AGV\AGV-MAC\start_agv.sh

echo "========================================="
echo "        Iniciando Sistema AGV"
echo "========================================="

# Verificar se estamos na pasta correta
if [ ! -d "agv-backend" ] || [ ! -d "agv-frontend" ]; then
    echo "Erro: Execute este script na pasta raiz do projeto AGV-MAC"
    exit 1
fi

# Ativar ambiente virtual e iniciar backend
echo "Iniciando backend..."
cd agv-backend

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Ambiente virtual ativado"
else
    echo "Aviso: Ambiente virtual não encontrado. Usando Python global."
fi

python app.py &
BACKEND_PID=$!
echo "Backend rodando no PID: $BACKEND_PID (http://localhost:5000)"

cd ..

# Verificar se o frontend foi buildado
if [ -d "agv-frontend/build" ]; then
    echo "Servindo frontend buildado..."
    cd agv-frontend
    npx serve -s build -l 3000 &
    FRONTEND_PID=$!
    echo "Frontend rodando no PID: $FRONTEND_PID (http://localhost:3000)"
else
    echo "Build do frontend não encontrado. Iniciando modo desenvolvimento..."
    cd agv-frontend
    npm start &
    FRONTEND_PID=$!
    echo "Frontend (dev) rodando no PID: $FRONTEND_PID (http://localhost:3000)"
fi

echo "========================================="
echo "  Sistema AGV iniciado com sucesso!"
echo "  Backend:  http://localhost:5000"
echo "  Frontend: http://localhost:3000"
echo "========================================="
echo "Pressione Ctrl+C para parar todos os serviços"

# Função para cleanup quando o script for interrompido
cleanup() {
    echo ""
    echo "Parando serviços..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Serviços parados."
    exit 0
}

# Capturar sinais de interrupção
trap cleanup SIGINT SIGTERM

# Aguardar interrupção
wait