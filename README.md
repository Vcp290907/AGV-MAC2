# Sistema AGV - Carrinho Autônomo

## 🏗️ Arquitetura

```
AGV-Sistema/
├── 📁 agv-web/          # Sistema WEB (Computador)
├── 📁 agv-raspberry/    # Sistema EMBARCADO (Raspberry Pi)
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
cd agv-raspberry && python main.py      # Sistema de controle
```

## 🌐 Comunicação

- **Sistema Web**: `http://localhost:3000` (Frontend) + `http://localhost:5000` (API)
- **Sistema Raspberry**: `http://IP_RASPBERRY:8080` (API local)
- **Protocolo**: REST API + WebSocket para tempo real

## 📚 Documentação

Veja a pasta `docs/` para documentação detalhada de cada componente.
