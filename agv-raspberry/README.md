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
                                │ └─────────────┘ │
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

| Situação | Recomendação | Script | Confiabilidade |
|----------|-------------|---------|----------------|
| Ambiente gerenciado externamente | `install_ultra_simple.sh` | ✅ Máxima | ⭐⭐⭐⭐⭐ |
| Problemas de dependências | `install_ultra_simple.sh` | ✅ Máxima | ⭐⭐⭐⭐⭐ |
| Primeiro teste | `quick_start.sh` | ✅ Alta | ⭐⭐⭐⭐⭐ |
| Sem câmera/OpenCV | `install_basic.sh` | ✅ Boa | ⭐⭐⭐⭐ |
| Sistema completo | `install.sh` | ⚠️ Variável | ⭐⭐⭐ |
| Raspberry Pi antigo | `install_ultra_simple.sh` | ✅ Máxima | ⭐⭐⭐⭐⭐ |

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

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Status da API |
| GET | `/status` | Status completo do AGV |
| POST | `/execute` | Executar comando |
| GET | `/camera` | Status da câmera |
| POST | `/shutdown` | Desligar sistema |
| GET | `/logs` | Logs recentes |

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
- Conectar via USB: `/dev/ttyUSB0`
- Baudrate: 115200
- Protocolo: Serial JSON

### Câmera
- Porta USB ou CSI
- Resolução: 640x480
- FPS: 30

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

### Problema: Câmera não detectada
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

## 🎯 Próximos Passos

1. **Integração ESP32** - Controle de motores
2. **Visão Computacional** - Detecção de QR codes
3. **Navegação** - Algoritmos de planejamento de caminho
4. **Sensores** - Detecção de obstáculos
5. **Monitoramento** - Dashboard de performance