# Fluxograma - Descoberta Automática do Backend

## 🔄 Processo de Descoberta

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INICIALIZAÇÃO DO SISTEMA                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐                                  ┌─────────────────┐
│   PC (Backend)  │                                  │  Raspberry Pi   │
│                 │                                  │     (AGV)       │
└────────┬────────┘                                  └────────┬────────┘
         │                                                    │
         │  1. Inicia Flask (porta 5000)                     │
         │  2. Inicia Backend Announcer                      │
         │     (porta 37020 UDP)                             │
         │                                                    │
         │  ✅ Aguardando descoberta...                      │
         │                                                    │
         │                                                    │  3. Executa
         │                                                    │     agv_mission_control.py
         │                                                    │
         │                                                    │  4. Chama get_backend_ip()
         │                                                    │
         │                  DESCOBERTA                        │  5. Não tem cache
         │                                                    │
         │  6. Broadcast UDP: "AGV_DISCOVERY_REQUEST"        │
         │<───────────────────────────────────────────────────┤
         │         (porta 37020)                              │
         │                                                    │
         │  📨 Requisição recebida de 192.168.0.X            │
         │                                                    │
         │  7. Response JSON:                                 │
         │     {                                              │
         │       "service": "agv-backend",                    │
         │       "ip": "192.168.0.134",                       │
         │       "port": 5000,                                │
         │       "timestamp": 1234567890                      │
         │     }                                              │
         │ ───────────────────────────────────────────────────>│
         │                                                    │  ✅ Backend encontrado!
         │                                                    │     IP: 192.168.0.134
         │                                                    │     Porta: 5000
         │                                                    │
         │                VALIDAÇÃO HTTP                      │  8. Salva em cache
         │                                                    │
         │  9. GET /status                                    │
         │<───────────────────────────────────────────────────┤
         │         (porta 5000 TCP)                           │
         │                                                    │
         │  10. 200 OK: {"bateria": 90, "conexao": "ok"}     │
         │ ───────────────────────────────────────────────────>│
         │                                                    │  ✅ Conexão validada!
         │                                                    │
         │              SISTEMA OPERACIONAL                   │  11. Usa backend_url
         │                                                    │      para todas as chamadas
         │  GET /pedidos/ativo                                │
         │<───────────────────────────────────────────────────┤
         │                                                    │
         │  POST /agv/status                                  │
         │<───────────────────────────────────────────────────┤
         │                                                    │
         │  GET /agv/next_command                             │
         │<───────────────────────────────────────────────────┤
         │                                                    │
         │  ✅ Sistema totalmente funcional                  │
         │     sem configuração manual de IP!                │
         │                                                    │
```

## 🔀 Fluxo com Fallback

```
┌─────────────────────────────────────────────────────────────────────┐
│              DESCOBERTA COM FALLBACK PARA IP FIXO                    │
└─────────────────────────────────────────────────────────────────────┘

        Raspberry Pi inicia
              │
              ▼
      ┌───────────────┐
      │ get_backend_ip()│
      └───────┬─────────┘
              │
              ▼
      ┌───────────────────┐
      │  Tem cache?       │
      └───────┬───────────┘
              │
        ┌─────┴─────┐
        │           │
       Sim         Não
        │           │
        │           ▼
        │   ┌─────────────────────┐
        │   │ Descoberta automática│
        │   │   (UDP Broadcast)    │
        │   └──────────┬───────────┘
        │              │
        │        ┌─────┴─────┐
        │        │           │
        │     Sucesso    Timeout/Erro
        │        │           │
        │        │           ▼
        │        │   ┌─────────────────┐
        │        │   │  Usar IP fixo   │
        │        │   │ (backend_config) │
        │        │   └────────┬─────────┘
        │        │            │
        └────────┴────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ Retorna IP   │
         └──────────────┘
```

## ⚡ Cenários de Uso

### Cenário 1: Primeira execução
```
Raspberry → Broadcast → Backend responde → Cache IP → Usa IP
```

### Cenário 2: Execuções subsequentes
```
Raspberry → Verifica cache → Usa IP do cache
```

### Cenário 3: Backend offline
```
Raspberry → Broadcast → Timeout → Usa IP fixo de fallback
```

### Cenário 4: IP mudou
```
Raspberry → Limpa cache → Nova descoberta → Novo IP em cache
```

## 🛡️ Segurança

```
┌────────────────────────────────────────────────────┐
│              CAMADAS DE SEGURANÇA                  │
└────────────────────────────────────────────────────┘

1. Rede Local Apenas
   └─> Broadcast limitado à subnet local
   
2. Porta Dedicada
   └─> 37020 separada da API (5000)
   
3. Validação de Mensagem
   └─> Verifica "AGV_DISCOVERY_REQUEST"
   
4. Validação de Resposta
   └─> Verifica campo "service": "agv-backend"
   
5. Timeout
   └─> Evita bloqueios infinitos (5s default)
   
6. Fallback
   └─> IP fixo se descoberta falhar
```

## 📊 Performance

```
Tempo típico de descoberta:
├─ Rede WiFi: 0.5 - 2 segundos
├─ Rede Ethernet: 0.1 - 0.5 segundos
└─ Com retry (3x): 3 - 6 segundos

Overhead:
├─ Primeira execução: ~2 segundos
├─ Com cache: 0 segundos (instantâneo)
└─ Tamanho da mensagem: ~150 bytes
```

## 🔧 Componentes

```
┌─────────────────────────────────────────────────────┐
│                  ARQUITETURA                         │
└─────────────────────────────────────────────────────┘

Backend (PC):
├─ app.py
│  └─> Inicia Flask + Backend Announcer
├─ backend_announcer.py
│  └─> Servidor UDP (porta 37020)
│      ├─> Aguarda broadcasts
│      └─> Responde com IP/porta
└─ api/status.py
   └─> Endpoint /discovery/status

Raspberry Pi:
├─ backend_discovery.py
│  └─> Cliente UDP
│      ├─> Envia broadcasts
│      └─> Recebe respostas
├─ backend_config.py
│  └─> Configuração centralizada
│      ├─> Cache de IP descoberto
│      ├─> Fallback para IP fixo
│      └─> Funções get_backend_*()
└─ agv_mission_control.py
   └─> Usa get_backend_ip() automaticamente
```
