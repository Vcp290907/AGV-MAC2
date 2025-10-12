# AGV Raspberry Pi - Sistema de Controle

Sistema embarcado do AGV (Automated Guided Vehicle) que roda no Raspberry Pi, responsável por:
- Comunicação WiFi com o sistema PC
- Controle de motores via ESP32
- Processamento de visão computacional
- Navegação autônoma

## 💻 Desenvolvimento no Windows

O sistema pode ser desenvolvido e testado no Windows, embora alguns componentes específicos do Raspberry Pi não estejam disponíveis:

### Funcionalidades Disponíveis no Windows:
- ✅ **Visão Computacional**: Detecção de linha e QR codes usando webcam
- ✅ **Feedback Visual**: Display em tempo real com overlays
- ✅ **Simulação**: Navegação simulada sem hardware físico
- ❌ **Controle de Motores**: Requer ESP32 (modo simulação apenas)

### Configuração para Windows:

1. **Instalar dependências Python:**
```bash
pip install opencv-python pyzbar numpy
```

2. **Teste básico:**
```bash
python test_windows.py
```

3. **Demonstração visual:**
```bash
python demo_visual.py
```

4. **Menu completo:**
```bash
python line_following_navigation.py
```

### Limitações no Windows:
- Sem comunicação real com ESP32
- Usa webcam padrão em vez de Picamera2
- Motores não funcionam (simulação apenas)
- Alguns backends de câmera podem não funcionar

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
                                │ └─────────────┘ │
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

## 🔄 Sincronização de Desenvolvimento

Quando você faz mudanças no código no seu computador de desenvolvimento e precisa sincronizar com o Raspberry Pi:

### 📤 Método Automático (Recomendado)

1. **No seu computador Windows**, execute o script de sincronização:
   ```cmd
   cd agv-raspberry
   sync_to_raspberry.bat [usuario@ip_raspberry]
   ```
   
   Exemplo:
   ```cmd
   sync_to_raspberry.bat pi@192.168.1.100
   ```

2. **O script irá:**
   - ✅ Testar conexão SSH com o Raspberry Pi
   - 📦 Criar backup dos arquivos atuais
   - 📤 Enviar arquivos atualizados (`config.py`, `esp32_control.py`, etc.)
   - 🔍 Verificar sincronização
   - 🧪 Testar import das funções

### 🔧 Método Manual

Se preferir fazer manualmente:

1. **Conecte via SSH ao Raspberry Pi:**
   ```bash
   ssh pi@SEU_RASPBERRY_IP
   ```

2. **No Raspberry Pi, navegue para o diretório do projeto:**
   ```bash
   cd ~/Desktop/AGV/AGV-MAC2/agv-raspberry
   ```

3. **No seu computador, copie os arquivos via SCP:**
   ```bash
   # Copiar arquivos modificados
   scp config.py pi@SEU_RASPBERRY_IP:~/Desktop/AGV/AGV-MAC2/agv-raspberry/
   scp esp32_control.py pi@SEU_RASPBERRY_IP:~/Desktop/AGV/AGV-MAC2/agv-raspberry/
   scp mpu6050_integration.py pi@SEU_RASPBERRY_IP:~/Desktop/AGV/AGV-MAC2/agv-raspberry/
   ```

4. **Teste as mudanças no Raspberry Pi:**
   ```bash
   python3 -c "from config import get_esp32_port, get_esp32_baudrate; print('Port:', get_esp32_port(), 'Baudrate:', get_esp32_baudrate())"
   ```

### ⚠️ Arquivos que Geralmente Precisam Sincronização:
- `config.py` - Configurações centralizadas
- `esp32_control.py` - Controle do ESP32
- `mpu6050_integration.py` - Integração com MPU6050
- `esp32_mpu6050_firmware.ino` - Firmware do ESP32

### 🔍 Verificação Pós-Sincronização:

Após sincronizar, sempre verifique se tudo está funcionando:

```bash
# No Raspberry Pi
cd ~/Desktop/AGV/AGV-MAC2/agv-raspberry

# Testar import das configurações
python3 -c "from config import get_esp32_port, get_esp32_baudrate, get_esp32_timeout; print('✅ Config OK')"

# Testar conexão ESP32
python3 test_esp32_connection.py

# Testar MPU6050
python3 mpu6050_integration.py
```