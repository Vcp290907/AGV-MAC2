# Fluxograma - Descoberta Automática dos ESP32

## 🔄 Processo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│              SISTEMA DE DESCOBERTA DOS ESP32                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐              ┌──────────────────┐
│  Raspberry Pi    │              │  ESP32 Motor     │
│                  │              │  (qualquer porta)│
└────────┬─────────┘              └────────┬─────────┘
         │                                 │
         │  1. Lista portas USB           │
         │     /dev/ttyUSB0               │
         │     /dev/ttyUSB1               │
         │                                 │
         │  2. Testa /dev/ttyUSB0         │
         │  {"comando":"identify"}         │
         │─────────────────────────────────>│
         │                                 │
         │  3. Recebe identificação        │
         │  {"type":"ESP32_MOTOR",...}     │
         │<─────────────────────────────────│
         │                                 │
         │  ✅ Motor mapeado: /dev/ttyUSB0│
         │                                 │
         ▼                                 │
                                           │
┌──────────────────┐              ┌──────────────────┐
│  Raspberry Pi    │              │  ESP32 Garra     │
│                  │              │  (qualquer porta)│
└────────┬─────────┘              └────────┬─────────┘
         │                                 │
         │  4. Testa /dev/ttyUSB1         │
         │  {"comando":"identify"}         │
         │─────────────────────────────────>│
         │                                 │
         │  5. Recebe identificação        │
         │  {"type":"ESP32_GARRA",...}     │
         │<─────────────────────────────────│
         │                                 │
         │  ✅ Garra mapeada: /dev/ttyUSB1│
         │                                 │
         ▼                                 │
                                           │
┌─────────────────────────────────────────┐
│  6. Salva em cache (esp32_ports.json)   │
│     {                                    │
│       "motor_port": "/dev/ttyUSB0",     │
│       "garra_port": "/dev/ttyUSB1"      │
│     }                                    │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  7. Sistema pronto para usar            │
│     - Motor em USB0                     │
│     - Garra em USB1                     │
│     - Cache válido                      │
└─────────────────────────────────────────┘
```

## 🔀 Cenário: Portas Trocadas

```
ANTES DA RECONEXÃO:
┌─────────────┐         ┌─────────────┐
│ /dev/ttyUSB0│ ──────> │ ESP32 Motor │
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐
│ /dev/ttyUSB1│ ──────> │ ESP32 Garra │
└─────────────┘         └─────────────┘

USUÁRIO DESCONECTA E RECONECTA OS CABOS...

APÓS RECONEXÃO (portas trocadas):
┌─────────────┐         ┌─────────────┐
│ /dev/ttyUSB0│ ──────> │ ESP32 Garra │ ⚠️
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐
│ /dev/ttyUSB1│ ──────> │ ESP32 Motor │ ⚠️
└─────────────┘         └─────────────┘

SISTEMA DETECTA MUDANÇA:
┌──────────────────────────────────────┐
│  Cache inválido detectado            │
│  → Inicia nova descoberta            │
│  → Testa USB0: "ESP32_GARRA"         │
│  → Testa USB1: "ESP32_MOTOR"         │
│  → Atualiza mapeamento               │
│  → Salva novo cache                  │
└──────────────────────────────────────┘

RESULTADO:
✅ Sistema funciona corretamente!
✅ Não precisa reconfigurar nada!
✅ Detecção automática!
```

## 📡 Protocolo de Comunicação

```
┌─────────────────────────────────────────────────────┐
│           PROTOCOLO DE IDENTIFICAÇÃO                 │
└─────────────────────────────────────────────────────┘

COMANDO: identify
┌─────────────────────────────────────┐
│ Raspberry → ESP32                   │
│ {"comando":"identify"}              │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ ESP32 → Raspberry                   │
│ {                                   │
│   "type": "ESP32_MOTOR",           │
│   "version": "1.0",                │
│   "status": "online",              │
│   "capabilities": "motor,buzzer"   │
│ }                                   │
└─────────────────────────────────────┘

COMANDO: status
┌─────────────────────────────────────┐
│ Raspberry → ESP32                   │
│ {"comando":"status"}                │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ ESP32 → Raspberry                   │
│ {                                   │
│   "type": "ESP32_MOTOR",           │
│   "status": "ok",                  │
│   "motor": "ready"                 │
│ }                                   │
└─────────────────────────────────────┘
```

## 🎯 Fluxo de Decisão

```
                    Iniciar Conexão
                          │
                          ▼
                  ┌───────────────┐
                  │ Cache existe? │
                  └───────┬───────┘
                          │
                ┌─────────┴─────────┐
                │                   │
              SIM                  NÃO
                │                   │
                ▼                   ▼
        ┌───────────────┐   ┌──────────────┐
        │ Testar cache  │   │  Descoberta  │
        │ (rápido)      │   │  completa    │
        └───────┬───────┘   └──────┬───────┘
                │                   │
        ┌───────┴───────┐          │
        │               │          │
    Cache OK?       Cache          │
     válido?        inválido       │
        │               │          │
       SIM             NÃO         │
        │               │          │
        └───────────────┴──────────┘
                │
                ▼
        ┌──────────────┐
        │ Portas       │
        │ identificadas│
        └──────┬───────┘
                │
                ▼
        ┌──────────────┐
        │ Conectar e   │
        │ usar         │
        └──────────────┘
```

## 🔧 Estrutura do Sistema

```
┌─────────────────────────────────────────────────────┐
│              CAMADAS DO SISTEMA                      │
└─────────────────────────────────────────────────────┘

CAMADA 1: Aplicação
┌──────────────────────────────────────────┐
│  agv_mission_control.py                  │
│  ├─ Usa esp32_control.py                │
│  └─ Não precisa saber sobre portas      │
└──────────────────────────────────────────┘
              │
              ▼
CAMADA 2: Controle (esp32_control.py)
┌──────────────────────────────────────────┐
│  ESP32Controller                         │
│  ├─ connect_esp32_motor()               │
│  ├─ connect_esp32_garra()               │
│  └─ Usa descoberta automática           │
└──────────────────────────────────────────┘
              │
              ▼
CAMADA 3: Descoberta (esp32_discovery.py)
┌──────────────────────────────────────────┐
│  ESP32Discovery                          │
│  ├─ discover_all()                      │
│  ├─ identify_esp32()                    │
│  ├─ save_to_config()                    │
│  └─ load_discovered_ports()             │
└──────────────────────────────────────────┘
              │
              ▼
CAMADA 4: Hardware
┌──────────────────────────────────────────┐
│  /dev/ttyUSB0 → ESP32 Motor             │
│  /dev/ttyUSB1 → ESP32 Garra             │
└──────────────────────────────────────────┘
```

## ⚡ Performance

```
┌─────────────────────────────────────────┐
│       TEMPOS DE DESCOBERTA              │
└─────────────────────────────────────────┘

Primeira vez (sem cache):
├─ Lista portas USB: 0.1s
├─ Testa porta 0: 0.5s
├─ Testa porta 1: 0.5s
├─ Salva cache: 0.05s
└─ Total: ~1.2s

Com cache válido:
├─ Carrega cache: 0.01s
├─ Valida porta 0: 0.3s
├─ Valida porta 1: 0.3s
└─ Total: ~0.6s

Cache inválido (reconexão):
├─ Detecta falha: 0.5s
├─ Nova descoberta: 1.2s
└─ Total: ~1.7s
```

## 🛡️ Redundância e Fallback

```
┌─────────────────────────────────────────────────────┐
│           ESTRATÉGIA DE FALLBACK                     │
└─────────────────────────────────────────────────────┘

Método 1: Identificação por comando
         ↓ (se falhar)
Método 2: Teste de comandos específicos
         ↓ (se falhar)
Método 3: Usar porta restante
         ↓ (se falhar)
Método 4: Ordem padrão (USB0=Motor, USB1=Garra)
         ↓ (se falhar)
Método 5: Configuração manual (config.json)
```
