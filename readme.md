# Sistema AGV (Automated Guided Vehicle)

Sistema completo para controle e monitoramento de um carrinho AGV com Raspberry Pi 5, incluindo dashboard web, API REST e controle de hardware.

## 🚀 Tecnologias

**Hardware:**
- Raspberry Pi 5
- Coral USB Accelerator
- ESP32 Mini
- Câmera

**Software:**
- **Backend:** Python Flask (API REST)
- **Frontend:** React + Tailwind CSS
- **Banco de Dados:** SQLite
- **IA:** TensorFlow Lite (Coral USB)

## 📋 Funcionalidades

### Perfis de Usuário

**Gerentes:**
- Controle
- Análise
- Armazém
- Configuração
- Status
- Rotina

**Funcionários:**
- Controle
- Status
- Rotina

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- Node.js 16+
- npm

### 1. Clone o repositório
```bash
git clone <>
cd AGV-MAC
```

### 2. Instale as dependências
```bash
# Instala concurrently na raiz
npm install

# Backend
cd agv-backend
pip install flask flask-cors
cd ..

# Frontend
cd agv-frontend
npm install
cd ..
```

## 🚀 Como executar

### Opção 1: Comando único (Recomendado)
```bash
npm run dev
```

### Opção 2: Separadamente
```bash
# Backend
npm run backend

# Frontend (em outro terminal)
npm run frontend
```

### Opção 3: Script Windows
```bash
.\start.bat
```

## 🌐 Acesso

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000

## 📁 Estrutura do Projeto

```
AGV-MAC/
├── agv-backend/           # API Flask
│   ├── api/              # Rotas da API
│   │   ├── auth.py       # Autenticação
│   │   └── status.py     # Status do sistema
│   ├── models/           # Modelos de dados
│   ├── utils/            # Utilitários
│   └── app.py           # Aplicação principal
├── agv-frontend/         # Interface React
│   └── src/
│       ├── components/   # Componentes reutilizáveis
│       ├── pages/        # Páginas (Login, Dashboard)
│       └── services/     # Serviços de API
├── package.json          # Scripts do projeto
├── start.bat            # Script Windows
└── README.md
```