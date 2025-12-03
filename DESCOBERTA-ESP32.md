# 🎯 Guia Rápido - Descoberta Automática dos ESP32

## Problema
ESP32s trocam de porta USB (`/dev/ttyUSB0` ↔ `/dev/ttyUSB1`) ao reconectar.

## Solução
Sistema identifica automaticamente qual é Motor e qual é Garra.

---

## 📝 Passo a Passo

### 1. Atualizar Firmware

#### ESP32 Motor
```cpp
// No início do ESPbaixo.ino
const char* ESP32_TYPE = "ESP32_MOTOR";

// Na função loop(), adicionar:
if (strcmp(cmd, "identify") == 0) {
    StaticJsonDocument<256> response;
    response["type"] = ESP32_TYPE;
    response["status"] = "online";
    serializeJson(response, Serial);
    Serial.println();
    return;
}
```

#### ESP32 Garra
```cpp
// No início do ESPcima.ino
const char* ESP32_TYPE = "ESP32_GARRA";

// Na função loop(), adicionar:
if (strcmp(cmd, "identify") == 0) {
    StaticJsonDocument<256> response;
    response["type"] = ESP32_TYPE;
    response["status"] = "online";
    serializeJson(response, Serial);
    Serial.println();
    return;
}
```

### 2. Testar no Serial Monitor

**Motor:**
```
Envie: {"comando":"identify"}
Recebe: {"type":"ESP32_MOTOR","status":"online"}
```

**Garra:**
```
Envie: {"comando":"identify"}
Recebe: {"type":"ESP32_GARRA","status":"online"}
```

### 3. Testar no Raspberry Pi

```bash
cd agv-raspberry
python3 test_esp32_discovery.py
```

### 4. Usar no Código

```python
from esp32_control import connect_esp32_motor, connect_esp32_garra

# Conecta automaticamente (descobre portas)
connect_esp32_motor()
connect_esp32_garra()
```

---

## ✅ Pronto!

Agora os ESP32s são identificados automaticamente, independente da porta USB!

## 🔧 Troubleshooting

**Não identifica?**
1. Verifique firmware atualizado
2. Teste no Serial Monitor
3. Baudrate deve ser 115200

**Portas trocadas?**
```bash
rm esp32_ports.json
python3 esp32_discovery.py
```

## 📚 Documentação Completa
`docs/descoberta-esp32.md`
