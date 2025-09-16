# 🕹️ Controle Manual do AGV

Este documento explica como usar os controles manuais básicos do AGV para testes de movimento.

## 📋 Visão Geral

Os controles manuais permitem testar o movimento básico do AGV através de comandos simples:
- **Mover para frente** por 1 segundo
- **Mover para trás** por 1 segundo

Estes controles são ideais para:
- Testar a conectividade PC ↔ Raspberry Pi ↔ ESP32
- Verificar se os motores estão funcionando
- Calibrar movimento básico antes de implementar navegação autônoma

## 🏗️ Arquitetura de Comunicação

```
Frontend (React) → Backend (Flask) → Raspberry Pi → ESP32 → Motores
     ↓                    ↓              ↓            ↓
   Botões UI        /agv/move_forward   /move_forward  GPIO PWM
   WebSocket        /agv/move_backward  /move_backward
```

## 🎮 Como Usar

### 1. Acesse a Interface Web

1. Certifique-se de que o backend está rodando:
   ```bash
   cd agv-web/backend
   python app.py
   ```

2. Abra o navegador em: `http://localhost:5000`

3. Faça login no sistema

4. Vá para a página **"Controle"**

### 2. Use os Controles Manuais

Na seção **"Controles Manuais do AGV"**, você verá:

#### Botão "Mover para Frente" (↑)
- **Cor**: Verde
- **Função**: Move o AGV para frente por 1 segundo
- **Endpoint**: `POST /agv/move_forward`

#### Botão "Mover para Trás" (↓)
- **Cor**: Vermelha
- **Função**: Move o AGV para trás por 1 segundo
- **Endpoint**: `POST /agv/move_backward`

### 3. Verificação Visual

- **Loading**: Botão mostra spinner durante execução
- **Feedback**: Alert confirma envio do comando
- **WebSocket**: Status atualizado em tempo real

## 🔧 Implementação Técnica

### Frontend (React)

```javascript
// Função para mover para frente
const moverParaFrente = async () => {
  const response = await fetch('http://localhost:5000/agv/move_forward', {
    method: 'POST'
  });
  const data = await response.json();
  alert('Comando enviado: ' + data.message);
};
```

### Backend (Flask)

```python
@raspberry_bp.route('/agv/move_forward', methods=['POST'])
def move_forward():
    return send_motor_command('forward', 1.0)

def send_motor_command(direction, duration):
    # Encontra Raspberry Pi conectado
    raspberry_data = connected_raspberries[list(connected_raspberries.keys())[0]]

    # Envia comando via HTTP
    response = requests.post(f"http://{raspberry_data['ip']}:8080/move_forward")

    return jsonify(response.json())
```

### Raspberry Pi (Flask)

```python
@app.route('/move_forward', methods=['POST'])
def move_forward():
    # Simula movimento (substituir por controle real do ESP32)
    result = execute_motor_command('forward', 1.0)
    return jsonify(result)

def execute_motor_command(direction, duration):
    # TODO: Implementar comunicação serial com ESP32
    # Por enquanto, apenas simula
    time.sleep(duration)
    return {'success': True, 'message': f'Movimento {direction} executado'}
```

## ⚙️ Configuração do ESP32

Para controle real dos motores, implemente no ESP32:

```cpp
// Exemplo básico de controle PWM
const int motorPin1 = 12;  // GPIO para motor 1
const int motorPin2 = 13;  // GPIO para motor 2

void moveForward(int duration) {
  digitalWrite(motorPin1, HIGH);
  digitalWrite(motorPin2, LOW);
  delay(duration * 1000);  // Converter para milissegundos
  stopMotors();
}

void moveBackward(int duration) {
  digitalWrite(motorPin1, LOW);
  digitalWrite(motorPin2, HIGH);
  delay(duration * 1000);
  stopMotors();
}
```

## 🔍 Monitoramento e Debug

### Logs no Backend
```bash
# Ver logs do Flask
tail -f /var/log/agv_system.log
```

### Teste Direto dos Endpoints
```bash
# Testar endpoint do backend
curl -X POST http://localhost:5000/agv/move_forward

# Testar endpoint do Raspberry Pi
curl -X POST http://192.168.0.17:8080/move_forward
```

### WebSocket Events
Os comandos geram eventos WebSocket:
```javascript
socketService.addEventListener('motor_command', (data) => {
  console.log('Comando de motor:', data);
});
```

## 🚨 Solução de Problemas

### Erro: "Nenhum Raspberry Pi conectado"
- **Causa**: Raspberry Pi não registrou no backend
- **Solução**: Execute `python next_steps.py` no Raspberry Pi

### Erro: "Erro de conexão com Raspberry Pi"
- **Causa**: Raspberry Pi não está acessível
- **Solução**: Verifique se está ligado e na mesma rede

### Erro: "Comando enviado mas sem movimento"
- **Causa**: ESP32 não implementado ou desconectado
- **Solução**: Verifique conexão serial e implementação no ESP32

### Botão fica carregando infinitamente
- **Causa**: Timeout na requisição
- **Solução**: Verifique conectividade de rede

## 📊 Próximos Passos

Após testar os controles manuais:

1. **Implementar ESP32**: Adicionar comunicação serial real
2. **Calibrar motores**: Ajustar velocidade e direção
3. **Adicionar sensores**: Ultrassônico para obstáculos
4. **Implementar navegação**: Algoritmos de pathfinding
5. **Integração com câmera**: Detecção de QR codes

## 🎯 Benefícios dos Controles Manuais

- ✅ **Teste rápido** da comunicação completa
- ✅ **Debug simplificado** de cada camada
- ✅ **Calibração** de movimento básico
- ✅ **Base sólida** para funcionalidades avançadas
- ✅ **Interface intuitiva** para testes

---

**💡 Dica**: Use estes controles para testar cada componente separadamente antes de implementar a navegação autônoma completa.