# 🧪 Teste de Comunicação PC-Raspberry Pi

Este guia explica como testar a comunicação entre o PC e o Raspberry Pi no sistema AGV.

## 📋 Pré-requisitos

1. **PC com backend rodando:**
   ```bash
   cd agv-web/backend
   python app.py
   ```

2. **Raspberry Pi com sistema instalado:**
   ```bash
   cd agv-raspberry
   python main.py
   ```

3. **Ambos na mesma rede WiFi**

## 🚀 Teste Rápido

### 1. Teste Básico de Conectividade

```bash
# No Raspberry Pi, execute:
python test_connection.py
```

Este script irá:
- ✅ Testar conexão com o PC
- ✅ Verificar API local do Raspberry
- ✅ Registrar Raspberry Pi no PC
- ✅ Enviar status de teste

### 2. Teste Manual via API

```bash
# Testar PC
curl http://192.168.0.100:5000/test

# Testar Raspberry Pi
curl http://localhost:8080/test

# Registrar Raspberry Pi
curl -X POST http://192.168.0.100:5000/agv/register \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.0.101",
    "port": 8080,
    "status": {"battery": 85, "status": "idle"}
  }'

# Ver Raspberry Pis conectados
curl http://192.168.0.100:5000/agv/connected
```

## 🔍 Diagnóstico de Problemas

### Problema: "Conexão com PC falhou"

**Possíveis causas:**
1. IP do PC incorreto
2. Backend não está rodando
3. Firewall bloqueando porta 5000
4. Rede WiFi diferente

**Soluções:**
```bash
# Verificar IP do PC
hostname -I  # No PC
ifconfig     # Ou ip addr show

# Testar conectividade básica
ping 192.168.0.100

# Verificar se backend está rodando
netstat -tlnp | grep :5000
```

### Problema: "API local não responde"

**Possíveis causas:**
1. Sistema AGV não está rodando
2. Porta 8080 ocupada
3. Erro no código

**Soluções:**
```bash
# Verificar se sistema está rodando
ps aux | grep python

# Verificar porta
netstat -tlnp | grep :8080

# Ver logs
tail -f /var/log/agv_system.log

# Reiniciar sistema
python main.py
```

### Problema: "Registro falhou"

**Possíveis causas:**
1. Dados de registro inválidos
2. Backend não aceitando conexões
3. Conflito de IP

**Soluções:**
```bash
# Verificar dados de registro
curl -X POST http://localhost:8080/status

# Testar endpoint de registro diretamente
curl -X POST http://192.168.0.100:5000/agv/register \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.0.101", "port": 8080}'
```

## 📊 Monitoramento em Tempo Real

### Logs do Sistema

```bash
# Raspberry Pi
tail -f /var/log/agv_system.log

# PC (se configurado)
tail -f /var/log/agv_pc.log
```

### Status via API

```bash
# Status do Raspberry Pi
curl http://localhost:8080/status

# Status geral do sistema
curl http://192.168.0.100:5000/status

# Pedidos ativos
curl http://192.168.0.100:5000/pedidos
```

## 🔧 Configuração de Rede

### Arquivo de Configuração

```json
// config.py ou /home/pi/agv_config.json
{
  "network": {
    "pc_ip": "192.168.0.100",
    "pc_port": 5000,
    "local_port": 8080,
    "auto_discovery": true
  }
}
```

### Descoberta Automática

O sistema tenta descobrir o PC automaticamente testando IPs comuns:
- 192.168.0.100-110
- 192.168.1.100-110
- 10.0.0.100-110

### Configuração Manual

```bash
# Variáveis de ambiente
export PC_IP=192.168.0.100
export PC_PORT=5000

# Ou modificar config.py
NETWORK_CONFIG = {
    'pc_ip': '192.168.0.100',
    'pc_port': 5000
}
```

## 📡 Fluxo de Comunicação

```
1. Raspberry Pi inicia
   ↓
2. Testa conexão com PC
   ↓
3. Registra-se no PC
   ↓
4. Envia heartbeats periódicos
   ↓
5. Recebe comandos do PC
   ↓
6. Executa comandos
   ↓
7. Envia confirmações
```

## 🎯 Comandos Suportados

### Do PC para Raspberry Pi

```json
{
  "type": "move",
  "data": {
    "x": 100,
    "y": 200,
    "speed": 50
  }
}
```

```json
{
  "type": "pickup_order",
  "order_id": 123,
  "items": [...]
}
```

### Do Raspberry Pi para PC

```json
{
  "agv_id": "AGV_01",
  "status": {
    "battery": 85,
    "position": {"x": 10, "y": 20},
    "status": "moving"
  }
}
```

## 🚨 Códigos de Erro

| Código | Descrição | Solução |
|--------|-----------|---------|
| 400 | Dados inválidos | Verificar JSON enviado |
| 404 | Endpoint não encontrado | Verificar URL |
| 500 | Erro interno | Verificar logs |
| 1001 | Conexão perdida | Verificar rede |
| 1002 | Comando inválido | Verificar formato |

## 📞 Suporte

Para problemas de comunicação:

1. Execute `python test_connection.py`
2. Verifique logs em `/var/log/agv_system.log`
3. Teste conectividade básica com `ping`
4. Verifique configuração de rede
5. Reinicie ambos os sistemas se necessário

**Lembre-se:** A comunicação WiFi requer que ambos os dispositivos estejam na mesma rede!