# 🚀 Guia de Upload - Firmware ESP32

## 📁 Arquivos Criados

- **`ESPbaixo_com_discovery.ino`** → ESP32 Motor (controle de motores)
- **`ESPcima_com_discovery.ino`** → ESP32 Garra (controle de servos)

---

## 📋 Pré-requisitos

### 1. Arduino IDE
- Download: https://www.arduino.cc/en/software
- Versão recomendada: 2.x ou 1.8.x

### 2. Suporte ESP32
```
Arduino IDE → File → Preferences → Additional Board Manager URLs:
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

Tools → Board → Boards Manager → Procurar "ESP32" → Install
```

### 3. Bibliotecas Necessárias

**ArduinoJson** (ambos ESP32):
```
Sketch → Include Library → Manage Libraries
Procurar: "ArduinoJson"
Instalar: ArduinoJson by Benoit Blanchon (versão 6.x)
```

**ESP32Servo** (apenas ESP32 Garra):
```
Sketch → Include Library → Manage Libraries
Procurar: "ESP32Servo"
Instalar: ESP32Servo by Kevin Harrington
```

---

## 🔧 Upload ESP32 Motor

### Passo 1: Conectar Hardware
1. Conecte ESP32 Motor ao PC via USB
2. Aguarde drivers instalarem (Windows)

### Passo 2: Abrir Código
```
File → Open → ESPbaixo_com_discovery.ino
```

### Passo 3: Configurar Arduino IDE
```
Tools:
├─ Board: "ESP32 Dev Module"
├─ Upload Speed: "115200"
├─ CPU Frequency: "240MHz (WiFi/BT)"
├─ Flash Frequency: "80MHz"
├─ Flash Mode: "QIO"
├─ Flash Size: "4MB (32Mb)"
├─ Partition Scheme: "Default 4MB with spiffs"
└─ Port: (selecione a porta COM do ESP32)
```

### Passo 4: Verificar Código
```
Sketch → Verify/Compile (ou Ctrl+R)
```

Deve aparecer: "Done compiling"

### Passo 5: Upload
```
Sketch → Upload (ou Ctrl+U)
```

Aguarde: "Hard resetting via RTS pin..."

### Passo 6: Testar
```
Tools → Serial Monitor
Baudrate: 115200
```

Digite: `{"comando":"identify"}`

Deve responder:
```json
{"type":"ESP32_MOTOR","version":"1.0","status":"online",...}
```

✅ **ESP32 Motor OK!**

---

## 🤖 Upload ESP32 Garra

### Passo 1: Desconectar ESP32 Motor
- Desconecte o ESP32 Motor do PC

### Passo 2: Conectar ESP32 Garra
1. Conecte ESP32 Garra ao PC via USB
2. Aguarde drivers instalarem

### Passo 3: Abrir Código
```
File → Open → ESPcima_com_discovery.ino
```

### Passo 4: Configurar Arduino IDE
```
Tools:
├─ Board: "ESP32 Dev Module"
├─ Upload Speed: "115200"
├─ CPU Frequency: "240MHz (WiFi/BT)"
├─ Flash Frequency: "80MHz"
├─ Flash Mode: "QIO"
├─ Flash Size: "4MB (32Mb)"
├─ Partition Scheme: "Default 4MB with spiffs"
└─ Port: (selecione a porta COM do ESP32)
```

### Passo 5: Verificar Código
```
Sketch → Verify/Compile (ou Ctrl+R)
```

Deve aparecer: "Done compiling"

### Passo 6: Upload
```
Sketch → Upload (ou Ctrl+U)
```

Aguarde: "Hard resetting via RTS pin..."

### Passo 7: Testar
```
Tools → Serial Monitor
Baudrate: 115200
```

Digite: `{"comando":"identify"}`

Deve responder:
```json
{"type":"ESP32_GARRA","version":"1.0","status":"online",...}
```

✅ **ESP32 Garra OK!**

---

## 🧪 Testes Individuais

### Testar ESP32 Motor

**Status:**
```json
{"comando":"status"}
```
Resposta: `{"type":"ESP32_MOTOR","status":"ok","motor":"ready",...}`

**Mover Frente:**
```json
{"comando":"mover_frente","velocidade":50}
```
Resposta: `{"type":"ESP32_MOTOR","status":"success","message":"Movendo para frente",...}`

**Parar:**
```json
{"comando":"parar"}
```
Resposta: `{"type":"ESP32_MOTOR","status":"success","message":"Motores parados",...}`

### Testar ESP32 Garra

**Status:**
```json
{"comando":"status"}
```
Resposta: `{"type":"ESP32_GARRA","status":"ok","servo":"ready",...}`

**Mover Servos:**
```json
{"comando":"move_servos","giro":90,"um":90,"dois":90,"garra":70,"tres":90}
```
Resposta: `{"type":"ESP32_GARRA","status":"success","message":"Servos movidos",...}`

**Abrir Garra:**
```json
{"comando":"abrir_garra"}
```
Resposta: `{"type":"ESP32_GARRA","status":"success","message":"Garra aberta",...}`

---

## ⚙️ Configuração de Pinos (Referência)

### ESP32 Motor (ESPbaixo_com_discovery.ino)

```cpp
// Motor Esquerdo
#define MOTOR_ESQ_PWM 25
#define MOTOR_ESQ_IN1 26
#define MOTOR_ESQ_IN2 27

// Motor Direito
#define MOTOR_DIR_PWM 32
#define MOTOR_DIR_IN1 33
#define MOTOR_DIR_IN2 14

// Buzzer
#define BUZZER_PIN 23
```

**⚠️ Ajuste estes pinos se seu hardware for diferente!**

### ESP32 Garra (ESPcima_com_discovery.ino)

```cpp
#define PIN_GIRO_GARRA 13  // Base giratória
#define PIN_MOTOR_UM 12    // Articulação 1
#define PIN_MOTOR_DOIS 14  // Articulação 2
#define PIN_MOTOR_GARRA 27 // Garra (abrir/fechar)
#define PIN_MOTOR_TRES 26  // Articulação 3
```

**⚠️ Ajuste estes pinos se seu hardware for diferente!**

---

## 🐛 Resolução de Problemas

### "Erro ao abrir porta serial"
**Causa:** Outra aplicação usando a porta
**Solução:** Feche Serial Monitor, Arduino IDE anterior, ou outros programas

### "espcomm_upload_mem failed"
**Causa:** ESP32 não entrou em modo bootloader
**Solução:** 
1. Desconecte ESP32
2. Segure botão BOOT
3. Conecte USB (ainda segurando BOOT)
4. Clique Upload
5. Solte BOOT quando começar upload

### "Compilation error: ArduinoJson.h: No such file"
**Causa:** Biblioteca não instalada
**Solução:** Instale ArduinoJson (ver seção Pré-requisitos)

### "Compilation error: ESP32Servo.h: No such file"
**Causa:** Biblioteca não instalada (ESP32 Garra)
**Solução:** Instale ESP32Servo (ver seção Pré-requisitos)

### Serial Monitor não mostra nada
**Causa:** Baudrate incorreto
**Solução:** Configure para 115200 no Serial Monitor

### ESP32 não responde a comandos
**Causa:** JSON mal formatado
**Solução:** Use aspas duplas, não esqueça vírgulas

---

## 🎯 Próximos Passos

Depois de fazer upload nos dois ESP32:

1. ✅ Conecte ambos ao Raspberry Pi
2. ✅ Execute: `python3 test_esp32_discovery.py`
3. ✅ Veja a descoberta automática funcionando!
4. ✅ Execute: `python3 agv_mission_control.py`

---

## 💡 Dicas

- ✅ Sempre verifique a porta COM correta em Tools → Port
- ✅ Se tiver múltiplos ESP32, faça upload um de cada vez
- ✅ Anote qual ESP32 é qual fisicamente (cole etiqueta)
- ✅ Guarde os arquivos .ino para futuras atualizações
- ✅ Faça backup do código antes de modificar

---

## 📚 Comandos Disponíveis

### ESP32 Motor
- `identify` - Identificação
- `status` - Status atual
- `mover_frente` - Mover para frente
- `mover_tras` - Mover para trás
- `girar_esquerda` - Girar à esquerda
- `girar_direita` - Girar à direita
- `parar` - Parar motores
- `buzzer` - Acionar buzzer

### ESP32 Garra
- `identify` - Identificação
- `status` - Status atual
- `move_servos` - Mover servos individuais
- `posicao_inicial` - Ir para posição inicial
- `posicao_estante` - Ir para posição de estante
- `posicao_repouso` - Ir para posição de repouso
- `abrir_garra` - Abrir garra
- `fechar_garra` - Fechar garra
- `executar_sequencia` - Executar sequência de movimentos

---

## ✅ Checklist Final

### ESP32 Motor
- [ ] ArduinoJson instalado
- [ ] ESPbaixo_com_discovery.ino aberto
- [ ] Board configurado: ESP32 Dev Module
- [ ] Porta selecionada corretamente
- [ ] Código compilado sem erros
- [ ] Upload bem-sucedido
- [ ] Teste identify funcionando
- [ ] Teste de movimento funcionando

### ESP32 Garra
- [ ] ArduinoJson instalado
- [ ] ESP32Servo instalado
- [ ] ESPcima_com_discovery.ino aberto
- [ ] Board configurado: ESP32 Dev Module
- [ ] Porta selecionada corretamente
- [ ] Código compilado sem erros
- [ ] Upload bem-sucedido
- [ ] Teste identify funcionando
- [ ] Teste de servos funcionando

### Raspberry Pi
- [ ] Ambos ESP32 conectados
- [ ] test_esp32_discovery.py executado
- [ ] Descoberta automática funcionando
- [ ] Sistema pronto para uso

🎉 **Pronto! Sistema completo funcionando!**
