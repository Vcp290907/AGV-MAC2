# 🔍 Guia Rápido - Descoberta Automática do Backend

## Como Usar

### 1. Inicie o Backend (PC)
```bash
cd agv-web/backend
python app.py
```

✅ O servidor de descoberta inicia automaticamente na porta 37020

### 2. Execute no Raspberry Pi
```bash
cd agv-raspberry
python3 agv_mission_control.py
```

✅ O IP do backend será descoberto automaticamente!

### 3. Teste a Descoberta
```bash
python3 test_backend_discovery.py
```

## Requisitos de Firewall

### Windows (PC)
```powershell
# Permitir porta UDP 37020
netsh advfirewall firewall add rule name="AGV Discovery" dir=in action=allow protocol=UDP localport=37020
```

### Linux (PC)
```bash
sudo ufw allow 37020/udp
```

## Solução de Problemas

### Backend não encontrado?

1. ✅ Backend rodando? `curl http://localhost:5000/status`
2. ✅ Mesma rede? `ping <IP_DO_PC>`
3. ✅ Firewall configurado?
4. ✅ Porta 37020 liberada?

### Forçar IP Fixo
Edite `agv-raspberry/backend_config.py`:
```python
BACKEND_IP = '192.168.0.XXX'  # Seu IP
```

## 📚 Documentação Completa
Veja: `docs/descoberta-automatica-backend.md`
