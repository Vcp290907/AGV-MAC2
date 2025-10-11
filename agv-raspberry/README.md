# AGV Raspberry Pi - Sistema de Controle

Sistema embarcado do AGV (Automated Guided Vehicle) que roda no Raspberry Pi, responsável por:
- Comunicação WiFi com o sistema PC
- Controle de motores via ESP32
- Processamento de visão computacional
- Navegação autônoma

## 🏗️ Arquitetura

```
┌─────────────────┐     WiFi     ┌─────────────────┐
│   💻 Sistema PC  │◄──────────►│ 🤖 Raspberry Pi  │
│   (Flask + DB)   │             │                 │
│                 │             │ ┌─────────────┐ │
│ ┌─────────────┐ │             │ │ API Local   │ │
│ │ Web + Mobile│ │             │ │ (Flask)     │ │
│ └─────────────┘ │             │ └─────────────┘ │
└─────────────────┘             │                 │
                                │ ┌─────────────┐ │
                                │ │ Controle    │ │
                                │ │ de Motores  │ │
             **Erro `ModuleNotFoundError: No module named 'pyzbar'` ou problemas com pyzbar:**
```bash
# Reinstalação completa do pyzbar
bash reinstall_pyzbar.sh

# Ou correção geral:
bash fix_python_deps.sh
```

**Erro `ModuleNotFoundError: No module named 'libcamera'`:**
```bash
# Corrigir conflito entre versões do picamera2
bash fix_picamera2_conflict.sh

# Ou instalar manualmente:
sudo apt install -y python3-libcamera python3-picamera2 libcamera-dev
# Depois remover do venv:
source venv/bin/activate
pip uninstall picamera2 -y
``` │ └─────────────┘ │
                                │                 │
                                │ ┌─────────────┐ │
                                │ │ Câmera +    │ │
                                │ │ OpenCV      │ │
                                │ └─────────────┘ │
                                └─────────────────┘
```

## 📋 Pré-requisitos

### Hardware
- Raspberry Pi 4 ou superior
- ESP32 conectado via USB
- Câmera USB ou CSI
- Fonte de alimentação adequada
- Cartão SD de pelo menos 16GB

### Software
- Raspberry Pi OS (64-bit recomendado)
- Python 3.8+
- Acesso root para GPIO

## 🚀 Instalação

### ⚡ Opção 1: ULTRA SIMPLES (MAIS CONFIÁVEL)

```bash
# Instalação mais básica possível
sudo bash install_ultra_simple.sh

# Instalar dependências Python essenciais
bash install_deps.sh
```

**Ideal para:** Qualquer situação, máxima compatibilidade
- ✅ Python 3 e pip apenas
- ✅ Estrutura de diretórios
- ✅ Sem dependências problemáticas
- ✅ Funciona em qualquer Raspberry Pi OS
- ✅ **Script automático de dependências**
- ❌ **Sem OpenCV** (pode ser instalado depois)

### ⚡ Opção 2: Instalação ULTRA Rápida (Fácil)

```bash
# Apenas instala Python e cria estrutura
sudo bash quick_start.sh
```

**Ideal para:** Testes rápidos, desenvolvimento inicial
- ✅ Python 3 e pip
- ✅ Estrutura de diretórios
- ✅ Permissões configuradas
- ❌ **Nenhuma dependência pesada**

### 🏗️ Opção 3: Instalação Básica (Equilibrada)

```bash
# Instala essencial sem OpenCV
sudo bash install_basic.sh
```

**Ideal para:** Desenvolvimento sem visão computacional
- ✅ Flask, comunicação, PySerial
- ✅ Pillow, NumPy para imagens básicas
- ✅ Ambiente virtual completo
- ❌ **Sem OpenCV** (evita problemas de dependências)

### 🔧 Opção 4: Instalação Completa (Avançada)

```bash
# Instala tudo incluindo OpenCV
sudo bash install.sh
```

**Ideal para:** Sistema completo com visão computacional
- ✅ Todas as dependências do sistema
- ✅ OpenCV para processamento de imagem
- ✅ Ambiente virtual Python
- ✅ Todas as bibliotecas necessárias
- ⚠️ **Pode falhar em sistemas com dependências desatualizadas**

### 🎯 Qual Escolher?

| Situação                         | Recomendação              | Script     | Confiabilidade |
| -------------------------------- | ------------------------- | ---------- | -------------- |
| Ambiente gerenciado externamente | `install_ultra_simple.sh` | ✅ Máxima   | ⭐⭐⭐⭐⭐          |
| Problemas de dependências        | `install_ultra_simple.sh` | ✅ Máxima   | ⭐⭐⭐⭐⭐          |
| Primeiro teste                   | `quick_start.sh`          | ✅ Alta     | ⭐⭐⭐⭐⭐          |
| Sem câmera/OpenCV                | `install_basic.sh`        | ✅ Boa      | ⭐⭐⭐⭐           |
| Sistema completo                 | `install.sh`              | ⚠️ Variável | ⭐⭐⭐            |
| Raspberry Pi antigo              | `install_ultra_simple.sh` | ✅ Máxima   | ⭐⭐⭐⭐⭐          |

### ⚠️ Importante: Ambiente Python Gerenciado

**Raspberry Pi OS Bookworm** tem proteção PEP 668 que impede instalação direta de pacotes Python:

```bash
# ❌ NÃO FUNCIONA (ambiente gerenciado)
pip install Flask

# ✅ FUNCIONA (ambiente virtual)
python3 -m venv venv
source venv/bin/activate
pip install Flask
```

**Todos os scripts foram atualizados para lidar com isso automaticamente!**

### 📦 Instalação do OpenCV (Opcional)

Se usou instalação rápida/básica e quer adicionar OpenCV:

```bash
# Opção 1: Via apt (mais rápido, mais compatível)
sudo apt install -y python3-opencv

# Opção 2: Via pip (mais recente, pode demorar)
source venv/bin/activate
pip install opencv-python --no-cache-dir
```

### 📦 Instalação do Picamera2 (Para câmeras chinesas CSI)

**IMPORTANTE**: Câmeras chinesas CSI genéricas requerem Picamera2, NÃO funcionam com V4L2/OpenCV:

```bash
# Instalar Picamera2 (já incluído em install.sh)
source venv/bin/activate
pip install picamera2

# Verificar instalação
python3 -c "from picamera2 import Picamera2; print('✅ Picamera2 OK')"

# Testar câmera chinesa CSI
python3 test_picamera2_chinese.py
```

### 🧪 Teste das Câmeras

Após a instalação, teste suas câmeras chinesas CSI:

```bash
# Teste ultra simples (mais rápido)
python3 test_quick.py

# Teste de resolução das câmeras
python3 test_resolution.py

# Teste básico das câmeras (recomendado primeiro)
python3 test_picamera2_chinese.py

# Teste do sistema dual camera AGV
python3 test_agv_dual_camera.py

# Visualização em tempo real (ambas as câmeras lado a lado)
python3 agv_camera_live.py
```

**Controles da visualização em tempo real:**
- `q` - Sair da visualização
- `s` - Salvar screenshot das câmeras

### 📦 Instalação para Leitura de QR Codes

Para usar o sistema de leitura de QR codes, instale as dependências específicas:

#### **Para Câmeras CSI (Raspberry Pi):**
```bash
# Correção completa para picamera2 (recomendado)
bash install_picamera2_fix.sh

# Ou instalar manualmente (Bookworm):
sudo apt install -y python3-picamera2 libcap-dev
pip install picamera2 --break-system-packages
```

#### **Para Câmeras USB/Webcam:**
```bash
# Instalar dependências básicas
bash install_qr_simple.sh

# Ou instalar manualmente:
sudo apt install -y python3-opencv
pip install pyzbar Pillow
```

### 📦 Instalação Rápida de Dependências

Se você teve erro de "No module named 'flask_cors'", use este script:

```bash
# Instalar dependências essenciais automaticamente
bash install_deps.sh

# Ou instalar manualmente:
pip3 install --user flask flask-cors requests pyserial
```

### Instalação Manual

Se preferir instalar manualmente:

```bash
# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python e ferramentas básicas
sudo apt install -y python3 python3-pip python3-venv git build-essential

# 3. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependências Python
pip install -r requirements.txt
```

### 3. Configuração de Rede

#### Descobrir IP do PC Automaticamente

```bash
# Script automático de descoberta
python find_pc_ip.py

# Este script irá:
# ✅ Detectar a rede local
# ✅ Procurar PCs com backend rodando
# ✅ Testar conectividade
# ✅ Atualizar config.py automaticamente (opcional)
```

#### Configurar IP Manualmente

```bash
# No PC, descobrir o IP:
hostname -I  # Linux
ipconfig     # Windows (linha Ethernet/WiFi)

# No Raspberry Pi, editar config.py:
nano config.py
# Alterar: pc_ip = "192.168.0.100"  # IP do seu PC
```

#### Configurar WiFi (se necessário)

```bash
# Configurar WiFi (opcional, se não usar interface gráfica)
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Adicionar rede:
network={
    ssid="SUA_REDE_WIFI"
    psk="SUA_SENHA"
    key_mgmt=WPA-PSK
}
```

### 4. Configuração do Sistema AGV

```bash
# Criar diretório de dados
sudo mkdir -p /var/log
sudo mkdir -p /home/pi/agv_data

# Configurar permissões
sudo chown pi:pi /var/log/agv_system.log
sudo chown pi:pi /home/pi/agv_data

# Configurar execução automática (opcional)
sudo nano /etc/rc.local

# Adicionar antes de 'exit 0':
# su pi -c 'cd /home/pi/agv-raspberry && source venv/bin/activate && python main.py &'
```

## 🚀 Execução do Sistema

### ⚠️ **IMPORTANTE**: Ambiente Virtual

**TODOS os scripts Python devem ser executados com o ambiente virtual ativado:**

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Agora executar scripts Python
python qr_code_reader.py
python teste_qr_sistema.py
```

**Ou use o wrapper (ativa automaticamente):**
```bash
./run_python.sh qr_code_reader.py
```

**Para verificar se o ambiente virtual está funcionando:**
```bash
bash check_venv.sh
```

### Opções de Inicialização

O sistema oferece múltiplas formas de execução através do script `start_agv.sh`:

#### 1. **Execução Normal** (Recomendado para desenvolvimento)
```bash
bash start_agv.sh normal
# ou simplesmente:
python main.py
```
- ✅ Logs em tempo real no terminal
- ✅ Fácil interrupção com Ctrl+C
- ✅ Ideal para debugging

#### 2. **Execução em Background**
```bash
bash start_agv.sh background
```
- ✅ Sistema roda em segundo plano
- ✅ Libera o terminal para outros comandos
- ✅ Ideal para produção

#### 3. **Modo Debug**
```bash
bash start_agv.sh debug
```
- ✅ Logs detalhados (DEBUG level)
- ✅ Informações completas de troubleshooting
- ✅ Ideal para desenvolvimento avançado

#### 4. **Testes de Componentes**
```bash
bash start_agv.sh test
```
- ✅ Verifica se todos os módulos funcionam
- ✅ Testa comunicação e hardware
- ✅ Executa testes automatizados

#### 5. **Verificar Status**
```bash
bash start_agv.sh status
```
- ✅ Mostra se o sistema está rodando
- ✅ Exibe logs recentes
- ✅ Informações de processos ativos

#### 6. **Parar Sistema**
```bash
bash start_agv.sh stop
```
- ✅ Para qualquer instância em execução
- ✅ Limpeza graceful de recursos

### ⚠️ Importante: Permissões no Raspberry Pi

Para acesso completo ao hardware (câmeras, GPIO, etc.), execute como root:

```bash
sudo bash start_agv.sh normal
```

### 📊 Monitoramento

Após iniciar o sistema, você pode monitorar através dos logs:

```bash
# Logs do sistema
tail -f /var/log/agv_system.log

# Status da API local
curl http://localhost:8080/status
```

## ⚙️ Configuração

### Arquivo config.py

As configurações principais estão no arquivo `config.py`. Você pode modificar:

```python
# Rede
NETWORK_CONFIG = {
    'pc_ip': '192.168.0.100',  # IP do PC
    'pc_port': 5000,
    'local_port': 8080
}

# Hardware
HARDWARE_CONFIG = {
    'camera': {
        'enabled': True,
        'device': 0  # /dev/video0
    },
    'esp32': {
        'port': '/dev/ttyUSB0',
        'baudrate': 115200
    }
}
```

### Variáveis de Ambiente

```bash
# Configurar IP do PC
export PC_IP=192.168.0.100
export PC_PORT=5000

# Configurar WiFi
export WIFI_SSID=minha_rede
export WIFI_PASSWORD=minha_senha

# Configurar nível de log
export LOG_LEVEL=DEBUG
```

## 🎮 Como Usar

### 🚀 Método Automático (Recomendado)

```bash
# Execute este script - ele faz tudo automaticamente!
python next_steps.py

# O script irá:
# ✅ Verificar configuração
# ✅ Testar conexão com PC
# ✅ Registrar Raspberry Pi
# ✅ Iniciar sistema AGV
# ✅ Mostrar próximos passos
```

### 📋 Método Manual

#### 1. Verificar Configuração
```bash
# Verificar se IP do PC está configurado
cat config.py | grep pc_ip

# Se não estiver, execute:
python find_pc_ip.py
```

#### 2. Testar Conexão
```bash
# Testar comunicação com PC
python test_connection.py
```

#### 3. Iniciar Sistema
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar sistema em background
python main.py &
```

#### 4. Verificar Status
```bash
# Verificar se API está rodando
curl http://localhost:8080/status

# Verificar conexão com PC
curl http://localhost:8080/test

# Ver logs em tempo real
tail -f /var/log/agv_system.log
```

### 🎯 Após Configuração Bem-Sucedida

#### Acesse o Sistema:
- **Interface Web**: `http://SEU_PC_IP:5000`
- **API Local**: `http://localhost:8080`
- **Mobile App**: Use o aplicativo instalado

#### Funcionalidades Disponíveis:
- ✅ **Controle de pedidos** via interface web
- ✅ **Gerenciamento de armazém** (itens, localização)
- ✅ **Administração de usuários** (gerentes)
- ✅ **Monitoramento em tempo real**
- ✅ **Comunicação PC ↔ Raspberry Pi**
- ✅ **Detecção de QR codes** (até 4 simultâneos)

#### Monitoramento:
```bash
# Ver logs do sistema
tail -f /var/log/agv_system.log

# Ver processos ativos
ps aux | grep python

# Status da API
curl http://localhost:8080/status
```

#### Manutenção:
```bash
# Parar sistema
curl -X POST http://localhost:8080/shutdown

# Reiniciar
python main.py &

# Verificar conectividade
python test_connection.py
```

## 📡 API Local

### Endpoints Principais

| Método | Endpoint    | Descrição              |
| ------ | ----------- | ---------------------- |
| GET    | `/`         | Status da API          |
| GET    | `/status`   | Status completo do AGV |
| POST   | `/execute`  | Executar comando       |
| GET    | `/camera`   | Status da câmera       |
| POST   | `/shutdown` | Desligar sistema       |
| GET    | `/logs`     | Logs recentes          |

### Exemplos de Uso

```bash
# Status do sistema
curl http://localhost:8080/status

# Executar comando de movimento
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"type": "move", "data": {"x": 100, "y": 200}}'

# Desligar sistema
curl -X POST http://localhost:8080/shutdown
```

## 🔧 Desenvolvimento

### Estrutura de Arquivos

```
agv-raspberry/
├── main.py              # Sistema principal
├── api_local.py         # API Flask local
├── wifi_communication.py # Comunicação WiFi
├── config.py            # Configurações
├── requirements.txt     # Dependências
├── README.md           # Esta documentação
└── modules/            # Módulos específicos
    ├── camera.py       # Controle de câmera
    ├── motor_control.py # Controle de motores
    ├── navigation.py   # Algoritmos de navegação
    └── sensors.py      # Sensores
```

### Adicionando Novos Módulos

1. Criar arquivo em `modules/`
2. Importar no `main.py`
3. Integrar no loop principal

### Debug

```python
# Habilitar debug detalhado
import logging
logging.basicConfig(level=logging.DEBUG)

# Executar com debug
python main.py --debug
```

## 🔌 Conexões de Hardware

### ESP32
- **Conexão**: USB Serial (`/dev/ttyUSB0`)
- **Baudrate**: 115200
- **Protocolo**: JSON via Serial
- **Firmware**: Carregar `esp32_motor_control.ino`

#### Pinout dos Servo Motores:
```
ESP32 Pin → Função
1         → Servo Motor Esquerdo (PWM)
3         → Servo Motor Direito (PWM)
2         → LED Status (onboard)
```

#### Configuração dos Servos:
- **Servo Esquerdo (GPIO 1)**: 0° = frente, 180° = trás, 90° = parado
- **Servo Direito (GPIO 3)**: 180° = frente, 0° = trás, 90° = parado
- **Alimentação**: 5V e GND dos servos devem ser conectados adequadamente

#### Como Configurar ESP32:

1. **Instalar Arduino IDE**
2. **Instalar ESP32 Board**:
   - Arquivo → Preferências → URLs adicionais
   - Adicionar: `https://dl.espressif.com/dl/package_esp32_index.json`
   - Ferramentas → Placa → ESP32 Dev Module

3. **Carregar Firmware**:
   ```bash
   # Abrir esp32_motor_control.ino no Arduino IDE
   # Selecionar porta correta (/dev/ttyUSB0)
   # Upload
   ```

4. **Testar Comunicação**:
    ```bash
    # No Raspberry Pi

    # 1. Detectar automaticamente a porta do ESP32
    python detect_esp32.py

    # 2. Testar comunicação básica
    python test_esp32_connection.py basic
    python test_esp32_connection.py motors
    python test_esp32_connection.py interactive

    # Ou especificar porta manualmente se auto-detecção falhar:
    python test_esp32_connection.py basic --port /dev/ttyUSB1
    ```

5. **Diagnosticar Servo Motores**:
    ```bash
    # Diagnóstico completo dos servos
    python diagnose_servos.py connection    # Testa conexão
    python diagnose_servos.py movement      # Testa movimento
    python diagnose_servos.py interactive   # Modo interativo/calibração

    # No modo interativo você pode:
    # f - Mover para frente
    # b - Mover para trás
    # l - Testar apenas servo esquerdo
    # r - Testar apenas servo direito
    # c - Calibração manual
    # t - Status dos servos
    ```

6. **Debug Comunicação Serial**:
    ```bash
    # Debug detalhado do que é enviado/recebido
    python debug_serial.py                    # Porta padrão (/dev/ttyACM0)
    python debug_serial.py /dev/ttyACM0       # Porta específica

    # Mostra exatamente os bytes enviados e recebidos
    # Útil para identificar problemas de parsing JSON
    ```

7. **Leitor com API do PC (NOVO - MAIS RECOMENDADO)**:
    ```bash
    # Versão que se conecta à API do PC via HTTP
    python qr_reader_with_api.py

    # Ou especificar IP do PC:
    python qr_reader_with_api.py 192.168.0.100 5000

    # Controles:
    # q - sair
    ```

    **Esta versão permite comunicação em tempo real:**
    - ✅ **Lê QR codes** com câmera CSI (seu código melhorado)
    - ✅ **Conecta à API** do PC via HTTP (não banco local)
    - ✅ **Consulta dados** em tempo real do sistema principal
    - ✅ **Permite atualizações** bidirecionais PC ↔ Raspberry
    - ✅ **Interface visual** com status da conexão
    - ✅ **Use esta versão para o sistema distribuído!**

8. **Leitor com Banco Local (Backup)**:
    ```bash
    # Versão que acessa banco SQLite diretamente
    python qr_reader_with_database.py
    ```

8. **Leitor OpenCV (Backup)**:
    ```bash
    # Versão que funciona sempre - usa webcam/USB
    python qr_reader_opencv_only.py

    # Usar câmera específica (opcional)
    python qr_reader_opencv_only.py 1  # câmera ID 1
    ```

9. **Navegação Básica (Linha Reta + Curvas 90°)**:
    ```bash
    # Navegação usando MPU6050 para orientação
    python navigation_basic.py

    # Menu interativo com opções:
    # 1. Teste em linha reta
    # 2. Teste de curva 90° direita
    # 3. Teste de curva 90° esquerda
    # 4. Executar rota quadrada completa
    # 5. Mostrar status do sensor
    ```

10. **Integração MPU6050 (Giroscópio)**:
    ```bash
    # Teste direto do giroscópio e acelerômetro
    python mpu6050_integration.py

    # Firmware ESP32 com MPU6050
    # Arquivo: esp32_mpu6050_firmware.ino
    # Carregar no ESP32 via Arduino IDE
    ```

11. **Outras Versões**:
    ```bash
    # Universal (testa CSI primeiro, depois USB)
    python qr_reader_final.py --visual

    # USB Simples
    python qr_reader_simple_usb.py --visual
    ```

### Câmera
- **Câmera 1 (camera_id=0)**: 640x480 (mais rápida, visão geral)
- **Câmera 2 (camera_id=1)**: 1280x720 (mais detalhada, maior resolução)
- **Câmeras chinesas CSI**: Usar Picamera2 (biblioteca oficial Raspberry Pi)
- **Câmeras USB**: OpenCV com V4L2
- FPS: 30
- **IMPORTANTE**: Câmeras chinesas CSI genéricas NÃO funcionam com V4L2/OpenCV. Use apenas Picamera2.

### Sensores (Opcional)
- Ultrassônico: GPIO 23 (Trigger), 24 (Echo)
- IMU MPU6050: I2C (0x68)

## 🚨 Troubleshooting

### Problema: Pacotes não encontrados (libjasper-dev, libqtgui4, libtbb2, etc.)
```bash
# SOLUÇÃO: Usar instalação ultra simples (mais confiável)
sudo bash install_ultra_simple.sh

# Ou usar instalação básica (sem OpenCV)
sudo bash install_basic.sh

# Evitar instalação completa se sistema for antigo
# sudo bash install.sh  # Pode falhar em sistemas antigos
```

### Problema: Erro "Unable to locate package"
```bash
# SOLUÇÃO: Atualizar lista de pacotes
sudo apt update

# Ou usar instalação que não depende desses pacotes
sudo bash install_ultra_simple.sh
```

### Problema: OpenCV falha ao instalar
```bash
# Instalar versão do repositório (mais rápida)
sudo apt install -y python3-opencv

# Ou tentar versão mais recente (mais demorada)
pip install opencv-python --no-cache-dir
```

### Problema: "Permission denied" no GPIO
```bash
# Executar como root
sudo python main.py

# Ou ajustar permissões
sudo usermod -a -G gpio pi
```

### Problema: Câmera chinesa CSI não detectada
```bash
# ✅ SOLUÇÃO PARA CÂMERAS CHINESAS CSI:
# Usar Picamera2 (NÃO V4L2/OpenCV)
pip install picamera2

# Testar câmera
python3 test_picamera2_chinese.py

# Para código AGV, usar:
from agv_camera import AGVDualCamera
camera = AGVDualCamera()
frames = camera.capture_frames()
```

### Problema: Câmera USB não detectada
```bash
# Verificar dispositivos
ls /dev/video*

# Instalar ferramentas
sudo apt install -y v4l-utils

# Verificar permissões
sudo usermod -a -G video pi
```

### Problema: ESP32 não conecta
```bash
# Verificar porta USB
ls /dev/ttyUSB*

# Verificar permissões
sudo usermod -a -G dialout pi

# Testar comunicação
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0', 115200); print('OK')"
```

### Problema: Erro de conectividade WiFi
```bash
# Verificar IP do PC
hostname -I  # No PC

# Testar ping
ping 192.168.0.100

# Verificar se backend está rodando
netstat -tlnp | grep :5000
```

### Problema: "No module named 'flask_cors'"
```bash
# SOLUÇÃO: Instalar dependências essenciais
bash install_deps.sh

# Ou instalar manualmente:
pip3 install --user flask flask-cors requests pyserial

# Verificar instalação:
python3 -c "import flask, flask_cors, requests, serial; print('✅ OK')"
```

### Problema: Dependências Python falham
```bash
# Atualizar pip
pip install --upgrade pip

# Instalar com --no-cache-dir
pip install --no-cache-dir -r requirements.txt

# Ou instalar pacotes individualmente
pip install Flask Flask-CORS requests pyserial Pillow
```

### Problema: WiFi não conecta
```bash
# Verificar redes disponíveis
sudo iwlist wlan0 scan

# Reiniciar serviço de rede
sudo systemctl restart dhcpcd
```

## 📊 Monitoramento

### Logs
- Localização: `/var/log/agv_system.log`
- Níveis: DEBUG, INFO, WARNING, ERROR
- Rotação automática

### Métricas
- Status da bateria
- Temperatura do sistema
- Uso de CPU/Memória
- Latência de rede

### Alertas
- Bateria baixa
- Perda de conexão
- Erro de hardware
- Falha de navegação

## 🔄 Atualização

```bash
# Parar sistema
curl -X POST http://localhost:8080/shutdown

# Atualizar código
git pull

# Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar
python main.py
```

## 📞 Suporte

Para problemas ou dúvidas:

### 📋 Documentação de Suporte:
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Soluções para problemas comuns
- **[CONNECTION_TEST.md](CONNECTION_TEST.md)** - Guia de teste de comunicação
- **README.md** - Esta documentação completa

### 🔍 Passos de Diagnóstico:
1. Verificar logs: `tail -f /var/log/agv_system.log`
2. Testar conectividade: `curl http://localhost:8080/test`
3. Verificar status do hardware
4. Consultar documentação específica do módulo

### 🚨 Problemas Comuns:
- **Pacotes não encontrados**: Use `install_ultra_simple.sh`
- **OpenCV falha**: Instale separadamente ou pule por enquanto
- **Conectividade WiFi**: Verifique IPs e portas
- **ESP32 não conecta**: Verifique permissões USB

## 📱 QR Codes

### Sistema de Detecção de QR Codes

O sistema AGV inclui detecção avançada de QR codes para navegação autônoma:

#### Funcionalidades:
- ✅ **Detecção simultânea** de até 4 QR codes
- ✅ **Leitura em tempo real** via câmera CSI
- ✅ **Processamento visual** com OpenCV + pyzbar
- ✅ **Interface de teste** para validação

#### Arquivos Relacionados:
- `qr_code_reader.py` - Classe principal para detecção
- `teste_qr_leitura.py` - Script de teste básico
- `teste_qr_sistema.py` - Teste de compatibilidade (PC + RPi)
- `teste_qr_raspberry.py` - Teste específico do Raspberry Pi
- `agv_camera.py` - Integração com sistema de câmera

#### Instalação das Dependências:

**Opção 1: Instalação Completa (Recomendada)**
```bash
# Instalar dependências específicas do QR codes
bash install_qr_deps.sh
```

**Opção 2: Instalação Simplificada (Mais Confiável)**
```bash
# Versão que evita problemas de compilação
bash install_qr_deps_simple.sh
```

> **Nota**: Se encontrar erro `libcap development headers`, use a opção simplificada que instala tudo via apt.

#### Como Usar:

```bash
# Teste básico (funciona no PC e Raspberry Pi)
python teste_qr_sistema.py

# Teste específico do Raspberry Pi (somente no RPi)
python teste_qr_raspberry.py

# Usar em código:
from qr_code_reader import QRCodeReader

reader = QRCodeReader(camera_id=0)
qr_codes = reader.detectar_qr_codes()
```

#### Geração de QR Codes:

Para gerar QR codes compatíveis com o sistema:

```bash
cd ../qr_code_generator
python gerador_qr_avancado.py
```

**Nota**: Use QR codes do tipo "visual sólido" para melhor compatibilidade com CAD/CAM.

#### Compatibilidade:
- ✅ **Raspberry Pi**: Sistema completo com câmera CSI
- ✅ **PC Windows**: Desenvolvimento e testes (sem câmera física)
- ✅ **Testes automatizados**: Scripts de validação para ambos os ambientes

#### Troubleshooting:

**Diagnóstico completo do sistema:**
```bash
# Verificar tudo de uma vez
bash diagnose_qr_system.sh
```

**Erro `ModuleNotFoundError: No module named 'pyzbar'` ou problemas com pyzbar:**
```bash
# Reinstalação completa do pyzbar
bash reinstall_pyzbar.sh

# Ou correção geral:
bash fix_python_deps.sh
```

**Erro `libcap development headers` ao instalar picamera2:**
```bash
# Script automático de correção
bash fix_libcap_error.sh

# Ou instalar manualmente:
sudo apt install -y libcap-dev python3-prctl build-essential
pip install picamera2
```

**Picamera2 não funciona:**
```bash
# Verificar se as câmeras estão conectadas
vcgencmd get_camera

# Testar câmera básica
raspistill -o test.jpg
```

## 🧹 Limpeza da Pasta (Executada)

A pasta `agv-raspberry/` foi limpa automaticamente, removendo **27 arquivos desnecessários** e mantendo apenas **16 arquivos essenciais**:

### 📁 Arquivos Mantidos (16):
- `main.py` - Sistema principal AGV
- `api_local.py` - API Flask local
- `agv_camera.py` - Módulo de câmera
- `esp32_control.py` - Controle ESP32
- `qr_reader_simple.py` - **NOVO**: Leitor simples de QR codes
- `test_agv_dual_camera.py` - Teste câmera dual
- `test_esp32_connection.py` - Teste ESP32
- `detect_esp32.py` - Detecção ESP32
- `esp32_motor_control.ino` - Firmware ESP32
- `requirements.txt` - Dependências Python
- `config.py` - Configurações
- `config.example.json` - Exemplo de configuração
- `install_basic.sh` - Instalação básica
- `quick_start.sh` - Início rápido
- `start_agv.sh` - Script de inicialização
- `README.md` - Esta documentação

### 🗑️ Arquivos Removidos (27):
Scripts de instalação problemáticos, testes duplicados, documentação redundante e arquivos de debug temporários.

## 🎯 Próximos Passos

1. **Integração ESP32** ✅ - Controle de motores funcionando
2. **Visão Computacional** ✅ - Detecção de QR codes implementada
3. **Navegação** - Algoritmos de planejamento de caminho
4. **Sensores** - Detecção de obstáculos
5. **Monitoramento** - Dashboard de performance