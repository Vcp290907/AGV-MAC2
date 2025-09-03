# AGV Web - Sistema de Interface

Sistema web para gerenciamento e monitoramento do AGV.

## 🏗️ Componentes

- **Frontend**: React + Tailwind CSS (Interface do usuário)
- **Backend**: Flask + SQLite (API e dados)

## 🚀 Execução

### Backend:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend:
```bash
cd frontend
npm install
npm start
```

## 📡 APIs

### Endpoints principais:
- `GET /itens` - Lista itens do armazém
- `POST /pedidos` - Cria novo pedido
- `GET /dispositivos` - Lista AGVs disponíveis
- `POST /agv/comando` - Envia comando para Raspberry

## 🌐 Comunicação com Raspberry

O backend web se comunica com o Raspberry Pi via HTTP:

```python
# Envio de comando para Raspberry
response = requests.post('http://IP_RASPBERRY:8080/executar', json={
    'tipo': 'mover',
    'destino': 'A1',
    'itens': [1, 2, 3]
})
```
