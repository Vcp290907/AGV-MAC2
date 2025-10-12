#!/bin/bash

# Script para sincronizar arquivos modificados do desenvolvimento para o Raspberry Pi
# Uso: ./sync_to_raspberry.sh [usuario@ip_raspberry]

RASPBERRY_HOST=${1:-"pi@raspberrypi.local"}
RASPBERRY_PATH="/home/pi/Desktop/AGV/AGV-MAC2/agv-raspberry"

echo "🔄 Sincronizando arquivos para Raspberry Pi: $RASPBERRY_HOST"

# Arquivos críticos que foram modificados
FILES_TO_SYNC=(
    "config.py"
    "esp32_control.py"
    "mpu6050_integration.py"
    "esp32_mpu6050_firmware.ino"
)

# Verificar se podemos conectar via SSH
echo "🔍 Testando conexão SSH..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$RASPBERRY_HOST" "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "❌ Erro: Não foi possível conectar ao Raspberry Pi via SSH"
    echo "💡 Verifique se:"
    echo "   - O Raspberry Pi está ligado e na rede"
    echo "   - SSH está habilitado: sudo raspi-config > Interface Options > SSH"
    echo "   - As credenciais estão corretas"
    exit 1
fi

echo "✅ Conexão SSH estabelecida"

# Criar backup no Raspberry Pi
echo "📦 Criando backup dos arquivos atuais..."
ssh "$RASPBERRY_HOST" "cd $RASPBERRY_PATH && mkdir -p backup && cp -r *.py backup/ 2>/dev/null || true"

# Sincronizar arquivos
echo "📤 Enviando arquivos atualizados..."
for file in "${FILES_TO_SYNC[@]}"; do
    if [ -f "$file" ]; then
        echo "  ↗️  $file"
        scp "$file" "$RASPBERRY_HOST:$RASPBERRY_PATH/"
    else
        echo "  ⚠️  Arquivo não encontrado: $file"
    fi
done

# Verificar se os arquivos foram atualizados
echo "🔍 Verificando sincronização..."
ssh "$RASPBERRY_HOST" "cd $RASPBERRY_PATH && ls -la config.py esp32_control.py"

# Testar import das funções
echo "🧪 Testando import das funções..."
ssh "$RASPBERRY_HOST" "cd $RASPBERRY_PATH && python3 -c 'from config import get_esp32_port, get_esp32_baudrate; print(\"✅ Import OK - Port:\", get_esp32_port(), \"Baudrate:\", get_esp32_baudrate())'"

echo ""
echo "🎉 Sincronização concluída!"
echo "💡 Agora você pode testar os scripts no Raspberry Pi:"
echo "   ssh $RASPBERRY_HOST"
echo "   cd $RASPBERRY_PATH"
echo "   python3 esp32_control.py"