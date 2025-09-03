# Arquitetura do Sistema AGV

## 🏗️ Visão Geral

O sistema AGV é dividido em **dois componentes principais** que se comunicam via WiFi:

```
┌─────────────────────┐     WiFi     ┌─────────────────────┐
│   💻 COMPUTADOR     │◄────────────►│  🤖 RASPBERRY PI    │
│                     │              │                     │
│ ┌─────────────────┐ │              │ ┌─────────────────┐ │
│ │   Frontend      │ │              │ │  Sistema de     │ │
│ │   React         │ │              │ │  Controle       │ │
│ └─────────────────┘ │              │ └─────────────────┘ │
│                     │              │                     │
│ ┌─────────────────┐ │              │ ┌─────────────────┐ │
│ │   Backend       │ │              │ │  Hardware       │ │
│ │   Flask + DB    │ │              │ │  ESP32 + GPIO   │ │
│ └─────────────────┘ │              │ └─────────────────┘ │
│                     │              │                     │
│                     │              │ ┌─────────────────┐ │
│                     │              │ │  Câmera +       │ │
│                     │              │ │  OpenCV         │ │
│                     │              │ └─────────────────┘ │
└─────────────────────┘              └─────────────────────┘
```

## 🖥️ Sistema Web (Computador)

### Responsabilidades:
- **Interface do usuário** (React)
- **Gestão de dados** (Pedidos, Itens, Usuários)
- **Dashboard e relatórios**
- **Comunicação com Raspberry Pi**

### Tecnologias:
- Frontend: React + Tailwind CSS
- Backend: Flask + SQLite
- Comunicação: HTTP/REST + WebSocket

### Estrutura:
```
agv-web/
├── frontend/          # Interface React
│   ├── src/pages/     # Páginas (Login, Dashboard, Controle)
│   ├── src/components/# Componentes reutilizáveis
│   └── package.json   # Dependências Node.js
│
└── backend/          # API Flask
    ├── api/          # Endpoints REST
    ├── models/       # Modelos de dados
    ├── database.py   # Configuração SQLite
    └── app.py        # Aplicação principal
```

## 🤖 Sistema Raspberry Pi

### Responsabilidades:
- **Controle físico** do carrinho
- **Processamento de visão** computacional
- **Navegação autônoma**
- **Interface com hardware** (ESP32, sensores)

### Tecnologias:
- Python 3.8+ com asyncio
- OpenCV para visão computacional
- pyserial para comunicação ESP32
- Flask para API local

### Estrutura:
```
agv-raspberry/
├── main.py           # Sistema principal
├── controle/         # Lógica de navegação
│   └── navegacao.py  # Algoritmos de movimento
├── hardware/         # Interface com ESP32
│   └── esp32_interface.py
├── camera/           # Sistema de visão
│   └── vision_system.py
├── comunicacao/      # API local
│   └── api_local.py
└── requirements.txt  # Dependências Python
```

## 🌐 Protocolo de Comunicação

### HTTP/REST para Comandos

**Sistema Web → Raspberry Pi:**
```http
POST http://IP_RASPBERRY:8080/executar
Content-Type: application/json

{
  "tipo": "mover",
  "destino": "A1",
  "itens": [1, 2, 3],
  "timestamp": 1693651200
}
```

**Raspberry Pi → Sistema Web:**
```json
{
  "success": true,
  "status": "em_andamento",
  "resultado": {
    "posicao_atual": {"x": 1.5, "y": 2.0},
    "destino": "A1",
    "progresso": 45
  }
}
```

### WebSocket para Tempo Real

**Status contínuo:**
```json
{
  "tipo": "status_update",
  "agv_id": "AGV_01",
  "posicao": {"x": 2.3, "y": 1.8, "orientacao": 90},
  "bateria": 75,
  "velocidade": 0.5,
  "status": "movendo",
  "timestamp": 1693651200
}
```

## 🔄 Fluxo de Operação

### 1. Criação de Pedido
```
Usuário (Web) → Frontend → Backend → Raspberry Pi → Execução Física
```

### 2. Monitoramento em Tempo Real
```
Raspberry Pi → WebSocket → Backend → Frontend → Usuário
```

### 3. Parada de Emergência
```
Usuário → Frontend → Backend → Raspberry Pi (timeout 5s)
```

## 📡 APIs Principais

### Sistema Web (localhost:5000)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/agv/enviar_comando` | POST | Envia comando para Raspberry |
| `/agv/status` | GET | Obtém status do AGV |
| `/agv/parar_emergencia` | POST | Para AGV imediatamente |
| `/pedidos` | POST | Cria novo pedido |
| `/itens` | GET | Lista itens disponíveis |

### Raspberry Pi (IP_RASPBERRY:8080)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/executar` | POST | Executa comando recebido |
| `/status` | GET | Retorna status atual |
| `/camera` | GET | Stream da câmera |

## 🔧 Configuração de Rede

### Descoberta Automática de IP
```python
# No backend web
import socket

def descobrir_raspberry():
    # Scan da rede local para encontrar Raspberry Pi
    for ip in range(1, 255):
        endereco = f"192.168.1.{ip}"
        try:
            response = requests.get(f"http://{endereco}:8080/status", timeout=1)
            if response.status_code == 200:
                return endereco
        except:
            continue
    return None
```

### Configuração Manual
```bash
# No Raspberry Pi - descobrir IP atual
hostname -I

# No sistema web - configurar IP do Raspberry
curl -X POST http://localhost:5000/agv/configurar_ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100"}'
```

## 🛡️ Tratamento de Erros

### Falha de Comunicação
- **Timeout**: Tentar 3 vezes com backoff
- **Conexão recusada**: Marcar AGV como offline
- **Perda de rede**: Buffer de comandos para reenvio

### Falhas de Hardware
- **ESP32 desconectado**: Parar movimento e alertar
- **Câmera inativa**: Modo degradado sem visão
- **Bateria baixa**: Retornar à base automaticamente

## 📊 Monitoramento

### Métricas Importantes
- **Latência de comunicação** (Web ↔ Raspberry)
- **Taxa de sucesso de comandos**
- **Tempo de resposta do AGV**
- **Status da bateria e hardware**

### Logs Estruturados
```python
logger.info("🚚 Comando executado", extra={
    "comando": "mover",
    "destino": "A1", 
    "duracao": 15.2,
    "sucesso": True
})
```

## 🚀 Vantagens desta Arquitetura

✅ **Escalabilidade**: Múltiplos Raspberry Pi por sistema web  
✅ **Manutenibilidade**: Componentes independentes  
✅ **Confiabilidade**: Falha de um não afeta o outro  
✅ **Performance**: Processamento distribuído  
✅ **Flexibilidade**: Fácil adição de novos AGVs
