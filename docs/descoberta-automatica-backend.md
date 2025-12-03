# Descoberta Automática do Backend

Sistema de descoberta automática do IP do backend usando UDP broadcast.

## 📋 Como Funciona

1. **Backend (PC)**: Inicia um servidor UDP que responde a requisições de descoberta
2. **Raspberry Pi**: Envia broadcast UDP na rede local procurando o backend
3. **Comunicação**: Backend responde com seu IP e porta
4. **Cache**: IP descoberto é armazenado em cache para uso posterior

## 🚀 Configuração

### No Backend (PC)

O backend já está configurado para iniciar automaticamente o servidor de descoberta quando você rodar o Flask:

```bash
cd agv-web/backend
python app.py
```

Você verá a mensagem:
```
📡 Backend Announcer iniciado
   IP: 192.168.x.x
   Porta Backend: 5000
   Porta Discovery: 37020
```

### No Raspberry Pi

Não é necessária configuração adicional! O `agv_mission_control.py` já está configurado para usar descoberta automática.

## 🧪 Testando

### Teste Manual no Raspberry Pi

```bash
cd agv-raspberry
python3 test_backend_discovery.py
```

Este script irá:
1. ✅ Tentar descobrir o backend
2. ✅ Testar conexão HTTP
3. ✅ Verificar endpoints da API
4. ✅ Mostrar estatísticas

### Teste do Cliente de Descoberta

```bash
# No Raspberry Pi
python3 backend_discovery.py
```

### Teste do Servidor (PC)

```bash
# No PC com backend
cd agv-web/backend
python3 backend_announcer.py server
```

## 📡 Portas Utilizadas

- **5000**: Backend Flask (HTTP)
- **37020**: Descoberta UDP (Broadcast)

## 🔧 Configuração Avançada

### Desabilitar Descoberta Automática

Se você quiser usar IP fixo, edite `backend_config.py`:

```python
from backend_config import enable_auto_discovery

# Desabilitar descoberta
enable_auto_discovery(False)

# Usar IP fixo
from backend_config import set_backend_ip, set_backend_port
set_backend_ip('192.168.0.100')
set_backend_port(5000)
```

### Limpar Cache

```python
from backend_config import clear_cache
clear_cache()  # Força nova descoberta
```

## 🐛 Resolução de Problemas

### Backend não encontrado

1. **Verificar rede**: Raspberry Pi e PC devem estar na mesma rede
   ```bash
   # No Raspberry Pi
   ping <IP_DO_PC>
   ```

2. **Firewall**: Certifique-se de que a porta 37020 (UDP) não está bloqueada
   - Windows: `netsh advfirewall firewall add rule name="AGV Discovery" dir=in action=allow protocol=UDP localport=37020`
   - Linux: `sudo ufw allow 37020/udp`

3. **Backend rodando**: Verifique se o backend está ativo
   ```bash
   # No PC
   curl http://localhost:5000/status
   ```

4. **Verificar logs**: Quando o Raspberry tenta descobrir, você deve ver no backend:
   ```
   📨 Requisição de descoberta #1 de 192.168.x.x
   ✅ Resposta enviada para 192.168.x.x
   ```

### Timeout na descoberta

- Aumentar timeout no código:
  ```python
  result = discovery.discover_backend(timeout=10)  # 10 segundos
  ```

### Múltiplos backends na rede

O sistema sempre usa o primeiro backend que responder. Se houver múltiplos:
1. Desligue os backends não desejados
2. Ou use IP fixo especificando manualmente

## 📊 Monitoramento

### Verificar status do announcer

```bash
curl http://<IP_BACKEND>:5000/discovery/status
```

Resposta:
```json
{
  "success": true,
  "announcer": {
    "running": true,
    "backend_ip": "192.168.0.134",
    "backend_port": 5000,
    "discovery_port": 37020,
    "request_count": 5
  }
}
```

## 🔄 Fluxo de Descoberta

```
┌─────────────┐                                    ┌──────────┐
│ Raspberry Pi│                                    │    PC    │
│   (AGV)     │                                    │ (Backend)│
└──────┬──────┘                                    └────┬─────┘
       │                                                │
       │  1. Broadcast: "AGV_DISCOVERY_REQUEST"        │
       │───────────────────────────────────────────────>│
       │             (UDP porta 37020)                  │
       │                                                │
       │  2. Response: {ip, port, timestamp}            │
       │<───────────────────────────────────────────────│
       │                                                │
       │  3. HTTP Request: GET /status                  │
       │───────────────────────────────────────────────>│
       │             (TCP porta 5000)                   │
       │                                                │
       │  4. Response: {bateria, conexao}               │
       │<───────────────────────────────────────────────│
       │                                                │
       │  ✅ Conexão estabelecida                       │
       │                                                │
```

## 🎯 Vantagens

- ✅ **Automático**: Não precisa configurar IP manualmente
- ✅ **Dinâmico**: Funciona mesmo se o IP do PC mudar
- ✅ **Simples**: Zero configuração no Raspberry
- ✅ **Rápido**: Descoberta em segundos
- ✅ **Confiável**: Sistema de retry integrado
- ✅ **Fallback**: Usa IP configurado se descoberta falhar

## 📝 Arquivos Principais

- **Backend**:
  - `backend_announcer.py`: Servidor de anúncio UDP
  - `app.py`: Integração com Flask
  
- **Raspberry Pi**:
  - `backend_discovery.py`: Cliente de descoberta
  - `backend_config.py`: Configuração centralizada com descoberta
  - `test_backend_discovery.py`: Script de testes

## 🔐 Segurança

- Sistema usa rede local apenas (não expõe para internet)
- Porta UDP separada da API principal
- Validação de mensagens de descoberta
- Timeout automático para evitar bloqueios

## 📚 Exemplos de Uso

### Uso Básico (Automático)

```python
from backend_config import get_backend_url
import requests

# IP descoberto automaticamente!
url = get_backend_url()
response = requests.get(f"{url}/status")
print(response.json())
```

### Uso Manual

```python
from backend_discovery import BackendDiscovery

discovery = BackendDiscovery()
result = discovery.discover_backend()

if result:
    ip, port = result
    print(f"Backend: {ip}:{port}")
```

### Com Retry

```python
result = discovery.discover_with_retry(max_attempts=5, retry_delay=3)
```
