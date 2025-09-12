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

### 1. Configuração do Sistema

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências do sistema
sudo apt install -y python3 python3-pip python3-venv git

# Instalar bibliotecas para câmera (se usar câmera USB)
sudo apt install -y v4l-utils

# Instalar OpenCV dependencies
sudo apt install -y libatlas-base-dev libjasper-dev libqtgui4 libqt4-test libhdf5-dev
```

### 2. Clonagem e Configuração

```bash
# Clonar repositório
git clone <repository-url>
cd agv-raspberry

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt
```

### 3. Configuração de Rede

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

### 1. Iniciar Sistema

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar sistema
python main.py
```

### 2. Verificar Status

```bash
# Verificar se API está rodando
curl http://localhost:8080/status

# Verificar conexão com PC
curl http://localhost:8080/test
```

### 3. Monitoramento

```bash
# Ver logs em tempo real
tail -f /var/log/agv_system.log

# Verificar processos
ps aux | grep python
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

### Problema: "Permission denied" no GPIO
```bash
# Executar como root
sudo python main.py
```

### Problema: Câmera não detectada
```bash
# Verificar dispositivos
ls /dev/video*

# Instalar driver
sudo apt install uv4l
```

### Problema: ESP32 não conecta
```bash
# Verificar porta USB
ls /dev/ttyUSB*

# Verificar permissões
sudo usermod -a -G dialout pi
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
1. Verificar logs em `/var/log/agv_system.log`
2. Testar conectividade: `curl http://localhost:8080/test`
3. Verificar status do hardware
4. Consultar documentação específica do módulo

## 🎯 Próximos Passos

1. **Integração ESP32** - Controle de motores
2. **Visão Computacional** - Detecção de QR codes
3. **Navegação** - Algoritmos de planejamento de caminho
4. **Sensores** - Detecção de obstáculos
5. **Monitoramento** - Dashboard de performance