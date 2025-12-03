# Troubleshooting - Descoberta Automática do Backend

## 🔍 Diagnóstico Rápido

Execute este checklist para identificar problemas:

```bash
# No Raspberry Pi
cd agv-raspberry
python3 test_backend_discovery.py
```

## 🐛 Problemas Comuns

### 1. ❌ "Backend não encontrado na rede"

#### Possíveis causas:

**a) Backend não está rodando**
```bash
# No PC, verificar:
curl http://localhost:5000/status

# Deve retornar: {"bateria": 90, "conexao": "ok"}
```

**Solução**: Inicie o backend
```bash
cd agv-web/backend
python app.py
```

---

**b) Firewall bloqueando porta 37020**

**Windows - Verificar regra:**
```powershell
netsh advfirewall firewall show rule name="AGV Backend Discovery"
```

**Adicionar regra:**
```powershell
# Execute como Administrador
netsh advfirewall firewall add rule name="AGV Backend Discovery" dir=in action=allow protocol=UDP localport=37020
```

**Linux - Verificar UFW:**
```bash
sudo ufw status
```

**Adicionar regra:**
```bash
sudo ufw allow 37020/udp
```

---

**c) Dispositivos em redes diferentes**

**Verificar conectividade:**
```bash
# No Raspberry Pi
ping <IP_DO_PC>

# Exemplo:
ping 192.168.0.134
```

**Verificar subnet:**
```bash
# Raspberry Pi
ip addr show

# PC (Windows)
ipconfig

# PC (Linux)
ip addr show
```

**Solução**: Certifique-se que ambos estão na mesma rede (ex: 192.168.0.x)

---

**d) Múltiplas interfaces de rede**

O PC pode ter múltiplos IPs (WiFi, Ethernet, VPN):
```
WiFi: 192.168.0.134
Ethernet: 192.168.1.50
VPN: 10.0.0.5
```

**Verificar qual IP o announcer está usando:**
```bash
# No PC
cd agv-web/backend
python3 backend_announcer.py server

# Veja a linha: "IP: X.X.X.X"
```

**Solução manual**: Especifique o IP correto em `backend_config.py`:
```python
BACKEND_IP = '192.168.0.134'  # IP correto
```

---

### 2. ⏰ "Timeout na descoberta"

#### Aumentar timeout

Edite `backend_discovery.py`:
```python
result = discovery.discover_backend(timeout=10)  # 10 segundos
```

#### Ou use retry automático

```python
result = discovery.discover_with_retry(max_attempts=5, retry_delay=3)
```

---

### 3. 🔄 "Backend encontrado mas conexão HTTP falha"

```
✅ Backend encontrado: 192.168.0.134:5000
❌ Erro na conexão HTTP
```

#### Possíveis causas:

**a) Firewall bloqueando porta 5000**

**Windows:**
```powershell
netsh advfirewall firewall add rule name="AGV Backend HTTP" dir=in action=allow protocol=TCP localport=5000
```

**Linux:**
```bash
sudo ufw allow 5000/tcp
```

---

**b) Backend não está escutando em todas as interfaces**

Verifique em `app.py`:
```python
# CORRETO:
socketio.run(app, host="0.0.0.0", port=5000)

# ERRADO:
socketio.run(app, host="127.0.0.1", port=5000)  # Só localhost!
```

---

### 4. 🔁 "Cache com IP antigo"

Se o IP do PC mudou mas o Raspberry continua tentando o antigo:

```python
# No código Python do Raspberry
from backend_config import clear_cache
clear_cache()
```

Ou reinicie o sistema.

---

### 5. 📡 "Múltiplos backends respondendo"

Se houver vários PCs com backend na mesma rede, o Raspberry usará o primeiro que responder.

**Solução 1**: Desligue os outros backends

**Solução 2**: Use IP fixo
```python
from backend_config import set_backend_ip, enable_auto_discovery

enable_auto_discovery(False)
set_backend_ip('192.168.0.134')  # Backend específico
```

---

## 🧪 Testes Detalhados

### Teste 1: Descoberta básica

```bash
# No Raspberry Pi
cd agv-raspberry
python3 -c "
from backend_discovery import BackendDiscovery
d = BackendDiscovery()
result = d.discover_backend(timeout=10)
print(f'Resultado: {result}')
"
```

**Esperado**: `Resultado: ('192.168.0.134', 5000)`

---

### Teste 2: Servidor de anúncio

```bash
# No PC
cd agv-web/backend
python3 backend_announcer.py server
```

**Esperado**:
```
📡 Backend Announcer iniciado
   IP: 192.168.0.134
   Porta Backend: 5000
   Porta Discovery: 37020
✅ Aguardando requisições...
```

Deixe rodando e execute o Teste 1 em outro terminal.

---

### Teste 3: Endpoint de status

```bash
# De qualquer máquina na rede
curl http://<IP_BACKEND>:5000/discovery/status
```

**Esperado**:
```json
{
  "success": true,
  "announcer": {
    "running": true,
    "backend_ip": "192.168.0.134",
    "backend_port": 5000,
    "discovery_port": 37020,
    "request_count": 3
  }
}
```

---

### Teste 4: Porta UDP aberta

**Windows:**
```powershell
netstat -an | findstr :37020
```

**Linux:**
```bash
sudo netstat -ulnp | grep 37020
```

**Esperado**: Deve mostrar uma linha com a porta 37020 em estado LISTENING

---

### Teste 5: Wireshark/tcpdump (avançado)

Capture tráfego UDP na porta 37020:

**Wireshark (Windows/Linux)**:
- Filtro: `udp.port == 37020`
- Inicie captura
- Execute descoberta no Raspberry
- Deve ver: request (broadcast) e response (unicast)

**tcpdump (Linux)**:
```bash
sudo tcpdump -i any udp port 37020 -v
```

---

## 📋 Checklist de Verificação

Use este checklist quando tiver problemas:

```
Backend (PC):
[ ] Backend está rodando? (curl localhost:5000/status)
[ ] Announcer iniciado? (veja logs do Flask)
[ ] Firewall liberado? (porta 37020 UDP)
[ ] Porta HTTP liberada? (porta 5000 TCP)
[ ] IP do PC conhecido? (ipconfig/ip addr)

Raspberry Pi:
[ ] Mesma rede que o PC? (ping <IP_PC>)
[ ] Arquivo backend_discovery.py existe?
[ ] Teste de descoberta passa? (test_backend_discovery.py)
[ ] Cache limpo? (clear_cache())
[ ] Timeout adequado? (5-10 segundos)

Rede:
[ ] Ambos na mesma subnet? (192.168.X.X)
[ ] Sem VPN ativa interferindo?
[ ] Router não bloqueia broadcast?
[ ] WiFi/Ethernet no modo correto?
```

---

## 🔧 Ferramentas de Diagnóstico

### Script de diagnóstico completo

Crie `diagnose_discovery.py`:

```python
#!/usr/bin/env python3
import socket
import subprocess
import platform
import requests

def diagnose():
    print("🔍 DIAGNÓSTICO DE DESCOBERTA AUTOMÁTICA")
    print("="*60)
    
    # 1. IP Local
    print("\n1. IP Local:")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"   ✅ {local_ip}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 2. Ping ao PC
    pc_ip = input("\n2. Digite o IP do PC backend: ").strip()
    cmd = "ping -n 1" if platform.system() == "Windows" else "ping -c 1"
    result = subprocess.run(f"{cmd} {pc_ip}", shell=True, capture_output=True)
    if result.returncode == 0:
        print(f"   ✅ Ping OK")
    else:
        print(f"   ❌ Ping falhou")
    
    # 3. Porta HTTP
    print(f"\n3. Testando porta HTTP (5000):")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((pc_ip, 5000))
        s.close()
        if result == 0:
            print(f"   ✅ Porta 5000 aberta")
        else:
            print(f"   ❌ Porta 5000 fechada")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 4. Backend HTTP
    print(f"\n4. Testando endpoint /status:")
    try:
        r = requests.get(f"http://{pc_ip}:5000/status", timeout=5)
        if r.status_code == 200:
            print(f"   ✅ Backend respondendo")
            print(f"   Dados: {r.json()}")
        else:
            print(f"   ⚠️ Status: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 5. Descoberta UDP
    print(f"\n5. Testando descoberta UDP:")
    try:
        from backend_discovery import BackendDiscovery
        d = BackendDiscovery()
        result = d.discover_backend(timeout=5)
        if result:
            print(f"   ✅ Descoberta OK: {result[0]}:{result[1]}")
        else:
            print(f"   ❌ Descoberta falhou")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    diagnose()
```

Execute:
```bash
python3 diagnose_discovery.py
```

---

## 📞 Suporte

Se nenhuma solução funcionou:

1. **Colete informações**:
   ```bash
   # No Raspberry Pi
   python3 diagnose_discovery.py > diagnostico.txt
   
   # No PC
   ipconfig > ip_pc.txt  # Windows
   ip addr > ip_pc.txt   # Linux
   ```

2. **Tente modo manual**:
   Em `backend_config.py`:
   ```python
   # Desabilitar descoberta temporariamente
   enable_auto_discovery(False)
   BACKEND_IP = '192.168.0.XXX'  # IP fixo do PC
   ```

3. **Verifique versão**:
   - Python 3.7+
   - Bibliotecas atualizadas

---

## 🎯 Solução Rápida (Manual)

Se tiver urgência e a descoberta não funcionar:

1. **Descubra IP do PC**:
   ```bash
   # Windows
   ipconfig
   
   # Linux
   hostname -I
   ```

2. **Configure manualmente**:
   ```python
   # agv-raspberry/backend_config.py
   BACKEND_IP = '192.168.0.134'  # SEU IP
   BACKEND_PORT = 5000
   ```

3. **Desabilite descoberta**:
   ```python
   # No início de agv_mission_control.py
   from backend_config import enable_auto_discovery
   enable_auto_discovery(False)
   ```

Isso fará o sistema funcionar imediatamente com IP fixo.
