# Guia de Instalação do Sistema AGV

## 🖥️ Instalação no Computador (Sistema Web)

### Pré-requisitos
- Python 3.8 ou superior
- Node.js 16 ou superior
- npm ou yarn
- Git

### 1. Configurar Backend
```bash
# Navegar para o diretório do backend
cd agv-web/backend

# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Inicializar banco de dados
python -c "from database import init_db; init_db()"

# Executar servidor
python app.py
```

### 2. Configurar Frontend
```bash
# Navegar para o diretório do frontend
cd agv-web/frontend

# Instalar dependências
npm install

# Executar em modo desenvolvimento
npm start

# Para build de produção
npm run build
```

### 3. Verificar Instalação Web
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Teste**: Fazer login na interface web

## 🤖 Instalação no Raspberry Pi

### Pré-requisitos Raspberry Pi
- Raspberry Pi 4 ou 5
- Raspbian OS (Bookworm ou posterior)
- Câmera habilitada
- Acesso SSH ou monitor conectado

### 1. Preparar Sistema Operacional
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências do sistema
sudo apt install python3-pip python3-venv git -y

# Instalar dependências do OpenCV
sudo apt install libopencv-dev python3-opencv -y

# Habilitar câmera (se necessário)
sudo raspi-config
# Interface Options > Camera > Enable
```

### 2. Instalar Sistema AGV
```bash
# Clonar repositório (ou copiar arquivos)
git clone <seu-repositorio> agv-sistema
cd agv-sistema/agv-raspberry

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Testar sistema
python main.py
```

### 3. Configurar como Serviço (Opcional)
```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/agv.service
```

```ini
[Unit]
Description=Sistema AGV
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/agv-sistema/agv-raspberry
Environment=PATH=/home/pi/agv-sistema/agv-raspberry/venv/bin
ExecStart=/home/pi/agv-sistema/agv-raspberry/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable agv.service
sudo systemctl start agv.service

# Verificar status
sudo systemctl status agv.service
```

## 🔧 Configuração de Rede

### 1. Descobrir IP do Raspberry Pi
```bash
# No Raspberry Pi
hostname -I
# Exemplo de saída: 192.168.1.100
```

### 2. Configurar IP no Sistema Web
```bash
# Método 1: Via API
curl -X POST http://localhost:5000/agv/configurar_ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100"}'

# Método 2: Editar arquivo de configuração
# Edite agv-web/backend/config.py
RASPBERRY_IP = "192.168.1.100"
```

### 3. Testar Comunicação
```bash
# Do computador para Raspberry Pi
curl http://192.168.1.100:8080/status

# Resposta esperada:
# {"ativo": true, "posicao": {...}, "bateria": 85}
```

## 🔌 Configuração do ESP32

### 1. Código básico para ESP32
```cpp
// Código Arduino para ESP32
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 AGV Pronto!");
}

void loop() {
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    
    if (comando == "PING") {
      Serial.println("PONG");
    } else if (comando == "BATERIA") {
      Serial.println("BATERIA:85");
    } else if (comando.startsWith("MOTOR:")) {
      // Processar comando de motor
      Serial.println("MOTOR:OK");
    } else if (comando == "PARAR") {
      // Parar motores
      Serial.println("PARAR:OK");
    }
  }
  
  delay(100);
}
```

### 2. Conectar ESP32 ao Raspberry Pi
```bash
# Verificar portas disponíveis
ls /dev/tty*

# Comum: /dev/ttyUSB0 ou /dev/ttyACM0
# Ajustar em agv-raspberry/hardware/esp32_interface.py:
# porta="/dev/ttyUSB0"
```

## 📷 Configuração da Câmera

### 1. Testar Câmera no Raspberry Pi
```bash
# Instalar utilitários de câmera
sudo apt install v4l-utils

# Listar câmeras disponíveis
v4l2-ctl --list-devices

# Testar captura
raspistill -o teste.jpg
```

### 2. Configurar OpenCV
```python
# Teste rápido do OpenCV
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print('✅ Câmera funcionando!')
    print(f'Resolução: {frame.shape}')
else:
    print('❌ Erro na câmera')
cap.release()
"
```

## 🧪 Testes de Integração

### 1. Teste Completo do Sistema
```bash
# Terminal 1: Iniciar backend web
cd agv-web/backend && python app.py

# Terminal 2: Iniciar frontend web  
cd agv-web/frontend && npm start

# Terminal 3: Iniciar sistema Raspberry (ou via SSH)
cd agv-raspberry && python main.py

# Terminal 4: Testar comunicação
curl -X POST http://localhost:5000/agv/enviar_comando \
  -H "Content-Type: application/json" \
  -d '{"tipo": "status"}'
```

### 2. Verificar Logs
```bash
# Logs do sistema web
tail -f agv-web/backend/app.log

# Logs do Raspberry Pi
tail -f agv-raspberry/system.log
# ou via systemctl:
sudo journalctl -u agv.service -f
```

## 🔥 Troubleshooting

### Problemas Comuns

**1. Erro de comunicação com Raspberry Pi**
```bash
# Verificar se o serviço está rodando
curl http://IP_RASPBERRY:8080/status

# Verificar firewall
sudo ufw status
sudo ufw allow 8080
```

**2. ESP32 não responde**
```bash
# Verificar permissões da porta serial
sudo usermod -a -G dialout $USER
sudo reboot

# Testar comunicação manual
screen /dev/ttyUSB0 115200
# Digite: PING
# Deve responder: PONG
```

**3. Câmera não funciona**
```bash
# Verificar se está habilitada
sudo raspi-config
# Interface Options > Camera > Enable

# Verificar módulo carregado
lsmod | grep bcm2835
```

**4. Dependências do OpenCV**
```bash
# Se erro de instalação do OpenCV
sudo apt install libatlas-base-dev libhdf5-dev libhdf5-serial-dev
pip install opencv-python==4.5.5.64
```

## 📊 Monitoramento de Saúde

### Script de Verificação
```bash
#!/bin/bash
# health_check.sh

echo "=== Verificação de Saúde do Sistema AGV ==="

# Verificar backend web
curl -s http://localhost:5000/status > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend Web: OK"
else
    echo "❌ Backend Web: FALHA"
fi

# Verificar Raspberry Pi
curl -s http://192.168.1.100:8080/status > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Raspberry Pi: OK"
else
    echo "❌ Raspberry Pi: FALHA"
fi

# Verificar ESP32 (se accessível via API)
python3 -c "
import serial
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    ser.write(b'PING\n')
    response = ser.readline().decode().strip()
    if 'PONG' in response:
        print('✅ ESP32: OK')
    else:
        print('❌ ESP32: SEM RESPOSTA')
    ser.close()
except:
    print('❌ ESP32: ERRO DE CONEXÃO')
"
```

A instalação está completa! 🚀
