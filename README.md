# Sistema AGV - Carrinho Autônomo

## 🏗️ Arquitetura

```
AGV-Sistema/
├── 📁 agv-web/          # Sistema WEB (Computador)
├── 📁 agv-raspberry/    # Sistema EMBARCADO (Raspberry Pi)
├── 📁 agv-shared/       # Bibliotecas compartilhadas
└── 📁 docs/             # Documentação
```

## 🚀 Execução Rápida

### Sistema Web (Computador):
```bash
cd agv-web/backend && python app.py     # Backend Flask
cd agv-web/frontend && npm start        # Frontend React
```

### Sistema Raspberry (Raspberry Pi):
```bash
cd agv-raspberry

# Opção 1: Execução direta
python main.py

# Opção 2: Script de inicialização (recomendado)
bash start_agv.sh normal

# Opção 3: Sistema em background
bash start_agv.sh background

# Opção 4: Modo debug com logs detalhados
bash start_agv.sh debug
```

## 🌐 Comunicação

- **Sistema Web**: `http://localhost:3000` (Frontend) + `http://localhost:5000` (API)
- **Sistema Raspberry**: `http://IP_RASPBERRY:8080` (API local)
- **Protocolo**: REST API + WebSocket para tempo real

## 🕹️ Controles Manuais do AGV

Teste básico de movimento através da interface web:

1. **Acesse**: `http://localhost:5000` → Página "Controle"
2. **Use os botões**:
   - **↑ Para Frente**: Move por 1 segundo
   - **↓ Para Trás**: Move por 1 segundo
3. **Arquitetura**: Frontend → Backend → Raspberry Pi → ESP32 → Motores

**Documentação completa**: [`docs/controle_manual_agv.md`](docs/controle_manual_agv.md)

##  Documentação

Veja a pasta `docs/` para documentação detalhada de cada componente.
