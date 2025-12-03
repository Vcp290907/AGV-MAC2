# 🔧 Atualização de Firmware - ESP32 com Descoberta Automática

## 📋 O que precisa ser feito

Atualizar o código Arduino dos dois ESP32 para responderem aos comandos de identificação.

## 🎯 Objetivo

Permitir que o Raspberry Pi identifique automaticamente qual ESP32 é o Motor e qual é a Garra.

---

## 📝 Passo a Passo Detalhado

### 1️⃣ ESP32 Motor (ESPbaixo.ino)

#### Passo 1.1: Abrir o código existente
```
Arduino IDE → File → Open → ESPbaixo.ino
```

#### Passo 1.2: Adicionar no INÍCIO do arquivo

Procure o início do código (após os `#include`) e adicione:

```cpp
// ============ IDENTIFICAÇÃO DO ESP32 (NOVO) ============
const char* ESP32_TYPE = "ESP32_MOTOR";
const char* ESP32_VERSION = "1.0";
// =======================================================
```

#### Passo 1.3: Modificar a função `loop()`

Procure a função `loop()` onde você processa comandos.

**ANTES** de processar outros comandos, adicione:

```cpp
void loop() {
    if (Serial.available() > 0) {
        String comando = Serial.readStringUntil('\n');
        comando.trim();
        
        StaticJsonDocument<256> doc;
        DeserializationError error = deserializeJson(doc, comando);
        
        if (error) {
            Serial.println("{\"error\":\"JSON inválido\"}");
            return;
        }
        
        const char* cmd = doc["comando"];
        
        // ============ ADICIONAR ESTE BLOCO (NOVO) ============
        // Comando de identificação
        if (strcmp(cmd, "identify") == 0 || 
            strcmp(cmd, "whoami") == 0 || 
            strcmp(cmd, "id") == 0) {
            
            StaticJsonDocument<256> response;
            response["type"] = ESP32_TYPE;
            response["version"] = ESP32_VERSION;
            response["status"] = "online";
            response["capabilities"] = "motor,buzzer,movement";
            
            serializeJson(response, Serial);
            Serial.println();
            return;
        }
        // ====================================================
        
        // Status - MODIFICAR para incluir type
        if (strcmp(cmd, "status") == 0) {
            StaticJsonDocument<256> response;
            response["type"] = ESP32_TYPE;  // ← ADICIONAR ESTA LINHA
            response["status"] = "ok";
            response["motor"] = "ready";
            // ... resto do seu código de status ...
            
            serializeJson(response, Serial);
            Serial.println();
            return;
        }
        
        // ... resto dos seus comandos ...
    }
}
```

#### Passo 1.4: Upload para o ESP32

1. Conecte o ESP32 Motor ao PC
2. Arduino IDE → Tools:
   - Board: **ESP32 Dev Module**
   - Port: (selecione a porta do ESP32)
3. Clique em **Upload** (→)
4. Aguarde "Done uploading"

#### Passo 1.5: Testar

1. Arduino IDE → Tools → Serial Monitor
2. Baudrate: **115200**
3. Digite: `{"comando":"identify"}`
4. Pressione ENTER
5. Deve aparecer: `{"type":"ESP32_MOTOR","version":"1.0","status":"online","capabilities":"motor,buzzer,movement"}`

✅ Se funcionou, ESP32 Motor está pronto!

---

### 2️⃣ ESP32 Garra (ESPcima.ino)

#### Passo 2.1: Abrir o código existente
```
Arduino IDE → File → Open → ESPcima.ino
```

#### Passo 2.2: Adicionar no INÍCIO do arquivo

```cpp
// ============ IDENTIFICAÇÃO DO ESP32 (NOVO) ============
const char* ESP32_TYPE = "ESP32_GARRA";
const char* ESP32_VERSION = "1.0";
// =======================================================
```

#### Passo 2.3: Modificar a função `loop()`

**ANTES** de processar outros comandos, adicione:

```cpp
void loop() {
    if (Serial.available() > 0) {
        String comando = Serial.readStringUntil('\n');
        comando.trim();
        
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, comando);
        
        if (error) {
            Serial.println("{\"error\":\"JSON inválido\"}");
            return;
        }
        
        const char* cmd = doc["comando"];
        
        // ============ ADICIONAR ESTE BLOCO (NOVO) ============
        // Comando de identificação
        if (strcmp(cmd, "identify") == 0 || 
            strcmp(cmd, "whoami") == 0 || 
            strcmp(cmd, "id") == 0) {
            
            StaticJsonDocument<256> response;
            response["type"] = ESP32_TYPE;
            response["version"] = ESP32_VERSION;
            response["status"] = "online";
            response["capabilities"] = "servo,garra,gripper";
            
            serializeJson(response, Serial);
            Serial.println();
            return;
        }
        // ====================================================
        
        // Status - MODIFICAR para incluir type
        if (strcmp(cmd, "status") == 0) {
            StaticJsonDocument<256> response;
            response["type"] = ESP32_TYPE;  // ← ADICIONAR ESTA LINHA
            response["status"] = "ok";
            response["servo"] = "ready";
            response["garra"] = "ready";
            // ... resto do seu código de status ...
            
            serializeJson(response, Serial);
            Serial.println();
            return;
        }
        
        // ... resto dos seus comandos ...
    }
}
```

#### Passo 2.4: Upload para o ESP32

1. Conecte o ESP32 Garra ao PC
2. Arduino IDE → Tools:
   - Board: **ESP32 Dev Module**
   - Port: (selecione a porta do ESP32)
3. Clique em **Upload** (→)
4. Aguarde "Done uploading"

#### Passo 2.5: Testar

1. Arduino IDE → Tools → Serial Monitor
2. Baudrate: **115200**
3. Digite: `{"comando":"identify"}`
4. Pressione ENTER
5. Deve aparecer: `{"type":"ESP32_GARRA","version":"1.0","status":"online","capabilities":"servo,garra,gripper"}`

✅ Se funcionou, ESP32 Garra está pronto!

---

## 🧪 Teste Final no Raspberry Pi

Agora que ambos os ESP32 estão atualizados:

### 1. Conectar ambos ao Raspberry Pi

Conecte os dois ESP32 ao Raspberry Pi via USB.

### 2. Executar teste de descoberta

```bash
cd ~/agv-raspberry
python3 test_esp32_discovery.py
```

### 3. Resultado esperado

```
🔍 INICIANDO DESCOBERTA AUTOMÁTICA DOS ESP32
====================================================
📍 Portas USB encontradas: 2
   📌 /dev/ttyUSB0
   📌 /dev/ttyUSB1

🔍 Testando porta: /dev/ttyUSB0
   📥 Resposta: {"type":"ESP32_MOTOR",...}
   ✅ Identificado como ESP32 MOTOR

🔍 Testando porta: /dev/ttyUSB1
   📥 Resposta: {"type":"ESP32_GARRA",...}
   ✅ Identificado como ESP32 GARRA

📊 RESULTADO DA DESCOBERTA
====================================================
🔧 ESP32 MOTOR: /dev/ttyUSB0
🤖 ESP32 GARRA: /dev/ttyUSB1
====================================================
✅ TODOS OS TESTES PASSARAM!
```

---

## 🔍 Troubleshooting

### Erro: "JSON inválido"

**Causa:** ArduinoJson não está instalado

**Solução:**
```
Arduino IDE → Sketch → Include Library → Manage Libraries
Procurar: ArduinoJson
Instalar: ArduinoJson by Benoit Blanchon (versão 6.x)
```

### Erro: "Não responde ao identify"

**Causa:** Código não foi atualizado corretamente

**Verificar:**
1. Constante `ESP32_TYPE` foi adicionada?
2. Bloco `if (strcmp(cmd, "identify")` foi adicionado?
3. Está ANTES dos outros comandos?
4. Upload foi bem-sucedido?

### Erro: "Ambos respondem como MOTOR"

**Causa:** Copiou código errado para Garra

**Solução:**
- ESP32 Motor deve ter: `const char* ESP32_TYPE = "ESP32_MOTOR";`
- ESP32 Garra deve ter: `const char* ESP32_TYPE = "ESP32_GARRA";`

### Erro: "Porta não encontrada"

**Causa:** Permissões de acesso à porta serial

**Solução:**
```bash
sudo usermod -a -G dialout $USER
sudo reboot
```

---

## 📝 Checklist de Atualização

### ESP32 Motor
- [ ] Abrir ESPbaixo.ino
- [ ] Adicionar `const char* ESP32_TYPE = "ESP32_MOTOR";`
- [ ] Adicionar comando `identify`
- [ ] Modificar comando `status` (incluir type)
- [ ] Upload para ESP32
- [ ] Testar no Serial Monitor
- [ ] Ver resposta com "ESP32_MOTOR"

### ESP32 Garra
- [ ] Abrir ESPcima.ino
- [ ] Adicionar `const char* ESP32_TYPE = "ESP32_GARRA";`
- [ ] Adicionar comando `identify`
- [ ] Modificar comando `status` (incluir type)
- [ ] Upload para ESP32
- [ ] Testar no Serial Monitor
- [ ] Ver resposta com "ESP32_GARRA"

### Raspberry Pi
- [ ] Conectar ambos os ESP32
- [ ] Executar `test_esp32_discovery.py`
- [ ] Verificar identificação correta
- [ ] Testar reconexão (trocar portas)
- [ ] Verificar re-descoberta automática

---

## 🎯 Arquivos de Referência

Se você tiver dúvidas, consulte os arquivos de exemplo completos:

- `ESP32_MOTOR_DISCOVERY_PATCH.ino` - Código completo do Motor
- `ESP32_GARRA_DISCOVERY_PATCH.ino` - Código completo da Garra

Eles contêm exemplos funcionais completos que você pode usar como referência.

---

## ✅ Pronto!

Depois de atualizar ambos os firmwares:

1. ✅ ESP32s se identificam automaticamente
2. ✅ Raspberry Pi detecta qual é qual
3. ✅ Sistema funciona mesmo trocando portas USB
4. ✅ Não precisa mais configurar manualmente

**Próximo passo:** Execute `python3 agv_mission_control.py` e veja a mágica acontecer! 🎉
