#!/bin/bash
"""
Script para executar todos echo ""
echo "8️⃣ TESTANDO QR Cecho ""
echo "9️⃣ TESTANDO QR CODES (se disponível)..."
echo "======================================"
if python3 -c "import pyzbar" 2>/dev/null; then
    python3 test_qr_codes.py
else
    echo "⚠️  pyzbar não instalado. Execute: pip3 install pyzbar"
fi

echo ""
echo "🔟 VERIFICANDO IMAGENS CRIADAS..."
echo "================================="ponível)..."
echo "======================================"
if python3 -c "import pyzbar" 2>/dev/null; then
    python3 test_qr_codes.py
else
    echo "⚠️  pyzbar não instalado. Execute: pip3 install pyzbar"
fi

echo ""
echo "9️⃣ VERIFICANDO IMAGENS CRIADAS..."
echo "=================================" câmera
Execute: bash run_all_camera_tests.sh
"""

echo "🚀 EXECUTANDO TODOS OS TESTES DE CÂMERA CSI"
echo "==========================================="

# Verificar se estamos no diretório correto
if [ ! -f "test_csi_camera.py" ]; then
    echo "❌ Arquivos de teste não encontrados. Execute no diretório agv-raspberry/"
    exit 1
fi

echo "1️⃣ VERIFICAÇÃO ULTRA RÁPIDA..."
echo "=============================="
python3 check_cameras.py

echo ""
echo "2️⃣ TESTE DE FOTO SIMPLES..."
echo "==========================="
python3 take_simple_photo.py

echo ""
echo "3️⃣ TESTE PICAMERA2 (CHINESA) 🎯..."
echo "=================================="
python3 test_picamera2_chinese.py

echo ""
echo "4️⃣ EXECUTANDO DIAGNÓSTICO COMPLETO..."
echo "====================================="
if [ -f "diagnose_csi_camera.sh" ]; then
    bash diagnose_csi_camera.sh
else
    echo "⚠️  Script diagnose_csi_camera.sh não encontrado"
fi

echo ""
echo "5️⃣ TENTATIVA DE CORREÇÃO AUTOMÁTICA..."
echo "======================================"
if [ -f "fix_csi_camera.sh" ]; then
    echo "🔧 Executando correções automáticas..."
    bash fix_csi_camera.sh
else
    echo "⚠️  Script fix_csi_camera.sh não encontrado"
fi

echo ""
echo "6️⃣ EXECUTANDO TESTE ESPECÍFICO CSI..."
echo "====================================="
python3 test_csi_camera.py

echo ""
echo "7️⃣ EXECUTANDO TESTE CSI CHINESA..."
echo "=================================="
python3 test_chinese_csi_camera.py

echo ""
echo "8️⃣ DIAGNÓSTICO DETALHADO CHINÊS..."
echo "=================================="
bash diagnose_chinese_csi.sh

echo ""
echo "9️⃣ TESTANDO QR CODES (se disponível)..."
echo "======================================"
if python3 -c "import pyzbar" 2>/dev/null; then
    python3 test_qr_codes.py
else
    echo "⚠️  pyzbar não instalado. Execute: pip3 install pyzbar"
fi

echo ""
echo "5️⃣ VERIFICANDO IMAGENS CRIADAS..."
echo "================================="
echo "Imagens de teste:"
ls -la *.jpg *.png 2>/dev/null || echo "Nenhuma imagem encontrada"

echo ""
echo "✅ TODOS OS TESTES CSI EXECUTADOS!"
echo ""
echo "📖 Consulte CAMERA_TEST_README.md para detalhes"
echo "🧪 Execute 'python3 test_csi_continuous.py' para teste contínuo"