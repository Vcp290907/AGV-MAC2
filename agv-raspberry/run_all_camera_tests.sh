#!/bin/bash
"""
Script para executar todos os testes de câmera
Execute: bash run_all_camera_tests.sh
"""

echo "🚀 EXECUTANDO TODOS OS TESTES DE CÂMERA CSI"
echo "==========================================="

# Verificar se estamos no diretório correto
if [ ! -f "test_csi_camera.py" ]; then
    echo "❌ Arquivos de teste não encontrados. Execute no diretório agv-raspberry/"
    exit 1
fi

echo "1️⃣ Verificando conexão CSI..."
if [ -f "check_csi_connection.sh" ]; then
    bash check_csi_connection.sh
else
    echo "⚠️  Script check_csi_connection.sh não encontrado"
fi

echo ""
echo "2️⃣ Instalando dependências..."
if [ -f "install_camera_deps.sh" ]; then
    bash install_camera_deps.sh
else
    echo "⚠️  Script install_camera_deps.sh não encontrado"
fi

echo ""
echo "3️⃣ Executando teste específico CSI..."
python3 test_csi_camera.py

echo ""
echo "4️⃣ Testando QR codes (se disponível)..."
if python3 -c "import pyzbar" 2>/dev/null; then
    python3 test_qr_codes.py
else
    echo "⚠️  pyzbar não instalado. Execute: pip3 install pyzbar"
fi

echo ""
echo "5️⃣ Verificando imagens criadas..."
echo "Imagens de teste:"
ls -la *.jpg *.png 2>/dev/null || echo "Nenhuma imagem encontrada"

echo ""
echo "✅ Todos os testes CSI executados!"
echo ""
echo "📖 Consulte CAMERA_TEST_README.md para detalhes"
echo "🧪 Execute 'python3 test_csi_continuous.py' para teste contínuo"