# 🔍 Descoberta Automática dos ESP32

Sistema que identifica automaticamente qual ESP32 é o **Motor** e qual é a **Garra**, mesmo quando eles trocam de porta USB.

## 📋 Problema Resolvido

**Antes:**
- ESP32 Motor em `/dev/ttyUSB0`, Garra em `/dev/ttyUSB1`
- Reconecta os cabos...
- Agora Motor está em `/dev/ttyUSB1`, Garra em `/dev/ttyUSB0` ❌
- Precisa reconfigurar manualmente!

**Agora:**
- Sistema identifica automaticamente qual é qual ✅
- Não importa qual porta USB você conectar ✅
- Funciona automaticamente ✅

## 🚀 Como Funciona

### 1. Identificação por Firmware

Cada ESP32 responde com seu tipo quando recebe comando de identificação:

```
Raspberry → ESP32: {"comando":"identify"}
ESP32 Motor → Raspberry: {"type":"ESP32_MOTOR",...}
ESP32 Garra → Raspberry: {"type":"ESP32_GARRA",...}
```

### 2. Descoberta Automática

O sistema:
1. Lista todas as portas USB
2. Testa cada porta enviando comando `identify`
3. Identifica qual é Motor e qual é Garra
4. Salva em cache para uso rápido

### 3. Cache Inteligente

- Primeira vez: ~5 segundos (testa todas as portas)
- Próximas vezes: instantâneo (usa cache)
- Reconexão: re-descobre automaticamente

## 🔧 Configuração

### Passo 1: Atualizar Firmware dos ESP32

#### ESP32 Motor (ESPbaixo.ino)

Adicione no **início do código**:
```cpp
const char* ESP32_TYPE = "ESP32_MOTOR";
```

Adicione na função **loop()** antes dos outros comandos:
```cpp
if (strcmp(cmd, "identify") == 0 || 
    strcmp(cmd, "whoami") == 0 || 
    strcmp(cmd, "id") == 0) {
    
    StaticJsonDocument<256> response;
    response["type"] = ESP32_TYPE;
    response["version"] = "1.0";
    response["status"] = "online";
    response["capabilities"] = "motor,buzzer,movement";
    
    serializeJson(response, Serial);
    Serial.println();
    return;
}
```

Modifique o comando **status** para incluir o tipo:
```cpp
if (strcmp(cmd, "status") == 0) {
    StaticJsonDocument<256> response;
    response["type"] = ESP32_TYPE;  // ← ADICIONAR
    response["status"] = "ok";
    response["motor"] = "ready";
    
    serializeJson(response, Serial);
    Serial.println();
    return;
}
```

#### ESP32 Garra (ESPcima.ino)

Adicione no **início do código**:
```cpp
const char* ESP32_TYPE = "ESP32_GARRA";
```

Adicione na função **loop()**:
```cpp
if (strcmp(cmd, "identify") == 0 || 
    strcmp(cmd, "whoami") == 0 || 
    strcmp(cmd, "id") == 0) {
    
    StaticJsonDocument<256> response;
    response["type"] = ESP32_TYPE;
    response["version"] = "1.0";
    response["status"] = "online";
    response["capabilities"] = "servo,garra,gripper";
    
    serializeJson(response, Serial);
    Serial.println();
    return;
}
```

Modifique o comando **status**:
```cpp
if (strcmp(cmd, "status") == 0) {
    StaticJsonDocument<256> response;
    response["type"] = ESP32_GARRA;  // ← ADICIONAR
    response["status"] = "ok";
    response["servo"] = "ready";
    
    serializeJson(response, Serial);
    Serial.println();
    return;
}
```

#### Código Completo

Veja os arquivos de exemplo:
- `ESP32_MOTOR_DISCOVERY_PATCH.ino`
- `ESP32_GARRA_DISCOVERY_PATCH.ino`

### Passo 2: Upload do Firmware

1. Abra Arduino IDE
2. Conecte cada ESP32
3. Selecione a placa: **ESP32 Dev Module**
4. Faça upload do código atualizado
5. Teste no Serial Monitor:
   ```
   Envie: {"comando":"identify"}
   Deve responder: {"type":"ESP32_MOTOR",...}
   ```

### Passo 3: Testar no Raspberry Pi

```bash
cd agv-raspberry
python3 test_esp32_discovery.py
```

Você verá:
```
🔍 INICIANDO DESCOBERTA AUTOMÁTICA DOS ESP32
📌 /dev/ttyUSB0
   📥 Resposta: {"type":"ESP32_MOTOR",...}
   ✅ Identificado como ESP32 MOTOR

📌 /dev/ttyUSB1
   📥 Resposta: {"type":"ESP32_GARRA",...}
   ✅ Identificado como ESP32 GARRA

✅ ESP32 MOTOR mapeado para: /dev/ttyUSB0
✅ ESP32 GARRA mapeado para: /dev/ttyUSB1
```

## 📝 Uso no Código

### Automático (Recomendado)

O sistema já está integrado no `esp32_control.py`:

```python
from esp32_control import connect_esp32_motor, connect_esp32_garra

# Conecta automaticamente (descobre as portas)
connect_esp32_motor()
connect_esp32_garra()
```

### Manual

Se quiser controle manual:

```python
from esp32_discovery import ESP32Discovery

# Descobrir portas
discovery = ESP32Discovery()
ports = discovery.discover_all()

# Usar portas descobertas
motor_port = ports['motor']  # Ex: '/dev/ttyUSB0'
garra_port = ports['garra']  # Ex: '/dev/ttyUSB1'
```

### Forçar Redescobrimento

Se você reconectar os ESP32:

```python
from esp32_control import rediscover_esp32_ports

# Força nova descoberta
ports = rediscover_esp32_ports()
```

## 🧪 Testes

### Teste Completo
```bash
python3 test_esp32_discovery.py
```

### Teste Rápido
```bash
python3 esp32_discovery.py
```

### Teste Individual
```python
from esp32_discovery import ESP32Discovery

discovery = ESP32Discovery()
result = discovery.discover_all()
print(f"Motor: {result['motor']}")
print(f"Garra: {result['garra']}")
```

## 🔄 Fluxo de Descoberta

```
┌─────────────────────────────────────────────────────┐
│         DESCOBERTA AUTOMÁTICA DOS ESP32              │
└─────────────────────────────────────────────────────┘

1. Sistema inicia
   ↓
2. Verifica cache (esp32_ports.json)
   ├─ Cache válido? → Usa portas do cache ✅
   └─ Cache inválido? → Continua descoberta
   ↓
3. Lista portas USB
   (/dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyACM0, ...)
   ↓
4. Para cada porta:
   ├─ Abre conexão serial
   ├─ Envia: {"comando":"identify"}
   ├─ Lê resposta
   └─ Verifica tipo: "ESP32_MOTOR" ou "ESP32_GARRA"
   ↓
5. Mapeamento completo:
   ├─ Motor → /dev/ttyUSB0
   └─ Garra → /dev/ttyUSB1
   ↓
6. Salva em cache (esp32_ports.json)
   ↓
7. Sistema pronto ✅
```

## 📂 Arquivos Principais

```
agv-raspberry/
├── esp32_discovery.py              # Sistema de descoberta
├── esp32_control.py                # Controle com descoberta integrada
├── test_esp32_discovery.py         # Testes completos
├── esp32_ports.json                # Cache das portas (gerado automaticamente)
├── ESP32_MOTOR_DISCOVERY_PATCH.ino # Exemplo de código para Motor
└── ESP32_GARRA_DISCOVERY_PATCH.ino # Exemplo de código para Garra
```

## 🐛 Resolução de Problemas

### ESP32 não identificado

**Verificar firmware:**
```bash
# Conecte apenas um ESP32
# Abra Serial Monitor (115200 baud)
# Digite: {"comando":"identify"}
# Deve responder com: {"type":"ESP32_MOTOR",...}
```

**Se não responder:**
1. Firmware não está atualizado
2. Baudrate incorreto (deve ser 115200)
3. ArduinoJson não instalado

### Identificação trocada

Se Motor for detectado como Garra:
1. Verifique a constante `ESP32_TYPE` no código
2. Certifique-se de fazer upload no ESP32 correto

### Portas trocadas após reboot

```bash
# Limpar cache e redescobrir
rm esp32_ports.json
python3 esp32_discovery.py
```

### Permissões de porta serial

```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER

# Reiniciar
sudo reboot
```

## ⚙️ Configuração Avançada

### Desabilitar descoberta automática

```python
from esp32_control import enable_auto_discovery

# Usar portas fixas (modo antigo)
enable_auto_discovery(False)
```

### Timeout customizado

```python
from esp32_discovery import ESP32Discovery

# Timeout de 5 segundos por porta
discovery = ESP32Discovery(baudrate=115200, timeout=5.0)
ports = discovery.discover_all()
```

### Portas específicas

```python
discovery = ESP32Discovery()

# Testar porta específica
device_type = discovery.identify_esp32('/dev/ttyUSB0')
print(f"Porta é: {device_type}")  # 'motor', 'garra' ou None
```

## 📊 Vantagens

- ✅ **Plug and Play**: Conecte em qualquer porta USB
- ✅ **Sem configuração**: Não precisa editar arquivos
- ✅ **Cache inteligente**: Rápido após primeira descoberta
- ✅ **Robusto**: Fallback se descoberta falhar
- ✅ **Fácil debug**: Logs detalhados
- ✅ **Compatível**: Funciona com código existente

## 🎯 Exemplo Prático

**Cenário**: Você reconecta os ESP32 e eles trocam de porta

**Sem descoberta automática:**
```python
# ❌ Motor agora está em USB1, mas código espera USB0
esp32_motor = ESP32Controller('/dev/ttyUSB0', ...)  # Erro!
```

**Com descoberta automática:**
```python
# ✅ Sistema descobre automaticamente a porta correta
connect_esp32_motor()  # Funciona independente da porta!
```

## 📚 Referências

- Código Motor: `ESP32_MOTOR_DISCOVERY_PATCH.ino`
- Código Garra: `ESP32_GARRA_DISCOVERY_PATCH.ino`
- Documentação API: `esp32_discovery.py`
- Testes: `test_esp32_discovery.py`
