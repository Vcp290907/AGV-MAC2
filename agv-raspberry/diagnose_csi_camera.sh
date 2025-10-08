#!/bin/bash
"""
Script de diagnóstico completo para câmera CSI no Raspberry Pi 5
Execute: bash diagnose_csi_camera.sh
"""

echo "🔍 DIAGNÓSTICO COMPLETO - CÂMERA CSI RASPBERRY PI 5"
echo "=================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo ""
echo "1️⃣ VERIFICAÇÃO BÁSICA DO SISTEMA"
echo "=================================="

# Verificar se está no Raspberry Pi
if [ ! -f "/proc/device-tree/model" ]; then
    echo -e "${RED}❌ Este não parece ser um Raspberry Pi${NC}"
    exit 1
fi

MODEL=$(tr -d '\0' < /proc/device-tree/model)
echo "📱 Modelo: $MODEL"

# Verificar arquitetura
ARCH=$(uname -m)
echo "💻 Arquitetura: $ARCH"

# Verificar kernel
KERNEL=$(uname -r)
echo "🔧 Kernel: $KERNEL"

echo ""
echo "2️⃣ VERIFICAÇÃO DA CÂMERA CSI"
echo "============================"

# Verificar detecção da câmera
echo "🔍 Verificando detecção da câmera..."
CAMERA_INFO=$(vcgencmd get_camera)
echo "   $CAMERA_INFO"

if echo "$CAMERA_INFO" | grep -q "detected=1"; then
    print_status 0 "Câmera CSI detectada"
else
    print_status 1 "Câmera CSI NÃO detectada"
    echo -e "${YELLOW}💡 Possíveis causas:${NC}"
    echo "   - Cabo flat não conectado"
    echo "   - Cabo flat danificado"
    echo "   - Conector da câmera danificado"
    echo "   - Câmera incompatível com Pi 5"
fi

echo ""
echo "3️⃣ VERIFICAÇÃO DE SOFTWARE"
echo "=========================="

# Verificar libcamera
echo "🔧 Verificando libcamera..."
if command -v libcamera-hello &> /dev/null; then
    LIBCAMERA_VERSION=$(libcamera-hello --version 2>&1 | head -1)
    print_status 0 "libcamera instalado: $LIBCAMERA_VERSION"
else
    print_status 1 "libcamera NÃO instalado"
fi

# Verificar GStreamer
echo "🎬 Verificando GStreamer..."
if command -v gst-launch-1.0 &> /dev/null; then
    GST_VERSION=$(gst-launch-1.0 --version 2>&1 | head -1)
    print_status 0 "GStreamer instalado: $GST_VERSION"
else
    print_status 1 "GStreamer NÃO instalado"
fi

# Verificar OpenCV
echo "🐍 Verificando OpenCV..."
python3 -c "
import sys
try:
    import cv2
    print('OpenCV versão:', cv2.__version__)
    print('✅ OpenCV instalado')
except ImportError as e:
    print('❌ OpenCV não instalado:', e)
    sys.exit(1)
" 2>/dev/null
OPENCV_STATUS=$?
print_status $OPENCV_STATUS "OpenCV Python"

echo ""
echo "4️⃣ VERIFICAÇÃO DE CONFIGURAÇÃO"
echo "=============================="

# Verificar config.txt
echo "📄 Verificando /boot/firmware/config.txt..."
if [ -f "/boot/firmware/config.txt" ]; then
    if grep -q "camera_auto_detect=1" /boot/firmware/config.txt; then
        print_status 0 "camera_auto_detect=1 encontrado"
    elif grep -q "start_x=1" /boot/firmware/config.txt; then
        print_status 0 "start_x=1 encontrado (método antigo)"
    else
        print_status 1 "Configuração da câmera NÃO encontrada em config.txt"
        echo -e "${YELLOW}💡 Adicione ao /boot/firmware/config.txt:${NC}"
        echo "   camera_auto_detect=1"
    fi
else
    print_status 1 "/boot/firmware/config.txt não encontrado"
fi

# Verificar grupo video
echo "👤 Verificando permissões do usuário..."
if groups $USER | grep -q video; then
    print_status 0 "Usuário no grupo 'video'"
else
    print_status 1 "Usuário NÃO está no grupo 'video'"
    echo -e "${YELLOW}💡 Execute: sudo usermod -a -G video $USER${NC}"
fi

echo ""
echo "5️⃣ VERIFICAÇÃO DE HARDWARE"
echo "=========================="

# Verificar dispositivos de vídeo
echo "📹 Dispositivos de vídeo disponíveis:"
ls -la /dev/video* 2>/dev/null || echo "   Nenhum dispositivo /dev/video* encontrado"

# Verificar módulos do kernel
echo "🔌 Módulos de câmera carregados:"
lsmod | grep -E "(bcm2835|v4l2|videodev)" || echo "   Nenhum módulo de câmera carregado"

echo ""
echo "6️⃣ TESTES FUNCIONAIS"
echo "===================="

# Teste básico com libcamera
echo "🧪 Teste básico com libcamera..."
if command -v libcamera-hello &> /dev/null; then
    echo "   Executando libcamera-hello -t 2000..."
    timeout 5 libcamera-hello -t 2000 &>/dev/null
    LIBCAMERA_TEST=$?
    print_status $LIBCAMERA_TEST "Teste libcamera-hello"
else
    print_status 1 "libcamera não disponível para teste"
fi

# Teste com OpenCV
echo "🧪 Teste básico com OpenCV..."
python3 -c "
import cv2
import sys
try:
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            print('✅ OpenCV conseguiu capturar frame')
        else:
            print('❌ OpenCV abriu câmera mas não conseguiu capturar')
            sys.exit(1)
    else:
        print('❌ OpenCV não conseguiu abrir câmera')
        sys.exit(1)
except Exception as e:
    print('❌ Erro no teste OpenCV:', e)
    sys.exit(1)
" 2>/dev/null
OPENCV_TEST=$?
print_status $OPENCV_TEST "Teste OpenCV"

echo ""
echo "7️⃣ LOGS DO SISTEMA"
echo "=================="

# Verificar logs relacionados à câmera
echo "📋 Últimas mensagens de log relacionadas à câmera:"
dmesg | grep -i camera | tail -5 || echo "   Nenhuma mensagem de câmera nos logs recentes"

echo ""
echo "8️⃣ DIAGNÓSTICO FINAL"
echo "==================="

echo "📊 RESUMO DO DIAGNÓSTICO:"
echo "========================"

# Contar problemas
ISSUES=0

if ! echo "$CAMERA_INFO" | grep -q "detected=1"; then
    echo -e "${RED}❌ Câmera não detectada${NC}"
    ((ISSUES++))
fi

if ! command -v libcamera-hello &> /dev/null; then
    echo -e "${RED}❌ libcamera não instalado${NC}"
    ((ISSUES++))
fi

if [ $OPENCV_STATUS -ne 0 ]; then
    echo -e "${RED}❌ OpenCV não funcionando${NC}"
    ((ISSUES++))
fi

if ! groups $USER | grep -q video; then
    echo -e "${RED}❌ Permissões insuficientes${NC}"
    ((ISSUES++))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ Nenhum problema crítico detectado${NC}"
    echo -e "${YELLOW}💡 Se ainda não funciona, pode ser problema de hardware${NC}"
else
    echo -e "${YELLOW}⚠️  $ISSUES problema(s) encontrado(s)${NC}"
fi

echo ""
echo "🔧 SOLUÇÕES RECOMENDADAS:"
echo "========================"

if ! echo "$CAMERA_INFO" | grep -q "detected=1"; then
    echo "1. ${YELLOW}VERIFICAR CONEXÃO FÍSICA:${NC}"
    echo "   - Certifique-se de que o cabo flat está conectado"
    echo "   - Verifique se o conector azul da câmera está voltado para o cabo USB"
    echo "   - Tente desconectar e reconectar o cabo"
    echo ""
fi

echo "2. ${YELLOW}HABILITAR CÂMERA NO SISTEMA:${NC}"
echo "   sudo raspi-config"
echo "   # Interfacing Options -> Camera -> Enable"
echo ""

echo "3. ${YELLOW}INSTALAR DEPENDÊNCIAS:${NC}"
echo "   bash install_camera_deps.sh"
echo ""

echo "4. ${YELLOW}CONFIGURAR PERMISSÕES:${NC}"
echo "   sudo usermod -a -G video $USER"
echo "   # Logout e login novamente"
echo ""

echo "5. ${YELLOW}REINICIAR SISTEMA:${NC}"
echo "   sudo reboot"
echo ""

echo "6. ${YELLOW}TESTAR NOVAMENTE:${NC}"
echo "   python3 test_csi_camera.py"
echo ""

echo "📞 SE AINDA NÃO FUNCIONAR:"
echo "=========================="
echo "- Verifique se a câmera é compatível com Raspberry Pi 5"
echo "- Teste com outra câmera CSI conhecida"
echo "- Verifique se o conector CSI da placa não está danificado"
echo "- Consulte: https://www.raspberrypi.com/documentation/computers/camera_software.html"