@echo off
REM Script para sincronizar arquivos modificados do desenvolvimento para o Raspberry Pi
REM Uso: sync_to_raspberry.bat [usuario@ip_raspberry]

setlocal enabledelayedexpansion

set "RASPBERRY_HOST=%~1"
if "%RASPBERRY_HOST%"=="" set "RASPBERRY_HOST=vcp2909@raspberrypi.local"
set "RASPBERRY_PATH=/home/vcp2909/Desktop/AGV/AGV-MAC2/agv-raspberry"

echo 🔄 Sincronizando arquivos para Raspberry Pi: %RASPBERRY_HOST%

REM Arquivos críticos que foram modificados
set "FILES_TO_SYNC=config.py esp32_control.py mpu6050_integration.py esp32_mpu6050_firmware.ino"

REM Verificar se podemos conectar via SSH (assumindo que scp/ssh estão disponíveis via Git Bash ou similar)
echo 🔍 Testando conexão SSH...
ssh -o ConnectTimeout=5 -o BatchMode=yes "%RASPBERRY_HOST%" "echo 'SSH OK'" >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Não foi possível conectar ao Raspberry Pi via SSH
    echo 💡 Verifique se:
    echo    - O Raspberry Pi está ligado e na rede
    echo    - SSH está habilitado: sudo raspi-config ^> Interface Options ^> SSH
    echo    - As credenciais estão corretas
    echo    - SSH/scp estão instalados no Windows ^(Git Bash, OpenSSH, etc.^)
    pause
    exit /b 1
)

echo ✅ Conexão SSH estabelecida

REM Criar backup no Raspberry Pi
echo 📦 Criando backup dos arquivos atuais...
ssh "%RASPBERRY_HOST%" "cd %RASPBERRY_PATH% && mkdir -p backup && cp -r *.py backup/ 2>/dev/null || true"

REM Sincronizar arquivos
echo 📤 Enviando arquivos atualizados...
for %%f in (%FILES_TO_SYNC%) do (
    if exist "%%f" (
        echo   ↗️  %%f
        scp "%%f" "%RASPBERRY_HOST%:%RASPBERRY_PATH%/"
    ) else (
        echo   ⚠️  Arquivo não encontrado: %%f
    )
)

REM Sincronizar também arquivos de sequência (*.json)
echo 📤 Enviando sequências (*.json)...
for %%f in (*.json) do (
    if exist "%%f" (
        echo   ↗️  %%f
        scp "%%f" "%RASPBERRY_HOST%:%RASPBERRY_PATH%/"
    )
)

REM Verificar se os arquivos foram atualizados
echo 🔍 Verificando sincronização...
ssh "%RASPBERRY_HOST%" "cd %RASPBERRY_PATH% && ls -la config.py esp32_control.py"

REM Testar import das funções
echo 🧪 Testando import das funções...
ssh "%RASPBERRY_HOST%" "cd %RASPBERRY_PATH% && python3 -c 'from config import get_esp32_port, get_esp32_baudrate; print(\"✅ Import OK - Port:\", get_esp32_port(), \"Baudrate:\", get_esp32_baudrate())'"

echo.
echo 🎉 Sincronização concluída!
echo 💡 Agora você pode testar os scripts no Raspberry Pi:
echo    ssh %RASPBERRY_HOST%
echo    cd %RASPBERRY_PATH%
echo    python3 esp32_control.py

pause