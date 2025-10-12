# Sistema de Navegação por Linha Preta + QR Codes

## 🏗️ Arquitetura do Sistema

O sistema de navegação do AGV foi completamente redesenhado para suportar o layout físico com linha reta e interseções em T para subcorredores.

### Componentes Principais

```
📦 Sistema de Navegação
├── 🎯 LineDetector - Detecção de linha preta
├── 🚗 LineFollowingNavigation - Navegação integrada
├── 🎮 AGVMissionControl - Controle de missões
└── 🤖 Main System - Coordenação geral
```

## 🛣️ Layout Físico do Armazém

### Estrutura Atual
- **Linha principal**: Fita isolante preta contínua no chão
- **Interseções**: 2 pontos em T formando subcorredores
- **Subcorredores**: Corredor01_01 e Corredor01_02
- **Prateleiras**: Posicionadas ao final de cada subcorredor
- **Ponto de entrega**: Área final com QR code "Entrega"

### Fluxo de Navegação
```
🚀 INÍCIO → 📏 Seguir linha → 🔀 Interseção detectada
    ↓
🔍 Verificar QR → ✅ Subcorredor correto → ➡️ Entrar subcorredor
    ↓
📦 Chegar à prateleira → 🤖 Coletar itens → ⬅️ Sair subcorredor
    ↓
📏 Seguir linha → 🔀 Próxima interseção → 🔄 Repetir
    ↓
🎯 Ponto de entrega → 📋 Finalizar missão
```

## 📷 Sistema de Visão

### Câmeras Utilizadas
- **Câmera inferior (ID 0)**: Detecção de linha preta no chão
- **Câmera superior (ID 1)**: Detecção de QR codes nas prateleiras

### LineDetector - Detecção de Linha

#### Funcionalidades
- **Pré-processamento**: Conversão HSV + filtro de cor preta
- **ROI**: Análise apenas da área inferior (60% da imagem)
- **Detecção**: Contornos + bounding box + validação de tamanho
- **PID**: Controle proporcional-integral-derivativo para correção de direção

#### Parâmetros de Configuração
```python
# Configurações de cor
lower_black = [0, 0, 0]
upper_black = [180, 255, 50]

# ROI
roi_y_start = height * 0.6  # 60% inferior

# PID
kp = 0.5, ki = 0.0, kd = 0.1

# Limites de linha
min_line_width = 10
max_line_width = 100
```

#### Algoritmo de Detecção
1. **Captura de frame** da câmera inferior
2. **Recorte ROI** (área inferior da imagem)
3. **Conversão HSV** para melhor detecção de cor
4. **Filtro de cor** para isolar pixels pretos
5. **Operações morfológicas** para limpar ruído
6. **Detecção de contornos** e seleção do maior
7. **Cálculo do centro** da linha detectada
8. **PID** para correção de direção

## 🚗 Navegação Integrada

### LineFollowingNavigation

#### Estados da Navegação
- **Seguindo linha**: Movimento contínuo com correção PID
- **Detectando interseção**: Monitoramento de expansão da linha
- **Verificando QR**: Leitura de códigos na interseção
- **Entrando subcorredor**: Curva 90° + avanço até prateleira
- **Saindo subcorredor**: Ré + curva -90°
- **Indo para entrega**: Navegação até ponto final

#### Métodos Principais
- `follow_line_step()`: Executa um passo de seguimento
- `detect_intersection()`: Detecta interseções na linha
- `navigate_to_intersection(target)`: Navega até subcorredor específico
- `enter_subcorredor()`: Entra no subcorredor
- `exit_subcorredor()`: Sai do subcorredor
- `navigate_to_delivery_point()`: Vai para entrega

#### Controle de Velocidade
```python
# Velocidades base
speed_base = 60  # 0-100
speed_min = 30   # Velocidade mínima
speed_max = 80   # Velocidade máxima

# Correção de direção
steering_sensitivity = 0.3  # Sensibilidade da direção
```

## 🎮 Controle de Missões

### AGVMissionControl Atualizado

#### Integração com Navegação por Linha
- **Navegação básica**: Movimentos simples (movimento em linha reta, curvas)
- **Navegação por linha**: Seguimento contínuo com detecção de QR
- **Detector QR**: Leitura de códigos nas prateleiras

#### Fluxo de Missão Atualizado
1. **Receber pedido** da API do PC
2. **Organizar rota** baseada nos subcorredores
3. **Para cada subcorredor**:
   - Navegar até interseção usando linha
   - Verificar QR code do subcorredor
   - Entrar no subcorredor
   - Coletar itens das prateleiras
   - Sair do subcorredor
4. **Ir para entrega** usando navegação por linha
5. **Finalizar missão**

## 🔧 Configuração e Calibração

### Calibração da Câmera de Linha
1. Posicionar câmera apontando para o chão
2. Ajustar altura para ver ~1-2m à frente
3. Calibrar filtro de cor preta
4. Ajustar ROI para área inferior
5. Testar detecção em diferentes condições de luz

### Calibração do PID
1. **Kp (Proporcional)**: Controla resposta imediata
2. **Ki (Integral)**: Corrige erro acumulado
3. **Kd (Derivativo)**: Previne oscilações

### Parâmetros de Distância
```python
distancia_ate_prateleira = 30  # cm após curva
tempo_busca_item = 5  # segundos para coleta
```

## 🧪 Testes e Validação

### Testes Individuais
- **LineDetector**: Teste de detecção isolada
- **LineFollowingNavigation**: Teste de seguimento básico
- **AGVMissionControl**: Teste de missão simulada

### Testes Integrados
- **Navegação completa**: Do início até entrega
- **Detecção de QR**: Em interseções e prateleiras
- **Recuperação de erro**: Perda de linha, QR não encontrado

### Cenários de Teste
1. **Linha reta**: Seguimento contínuo
2. **Interseção simples**: Detecção e decisão
3. **Subcorredor completo**: Entrada → coleta → saída
4. **Múltiplos subcorredores**: Rota complexa
5. **Entrega final**: Navegação até ponto final

## 🚨 Tratamento de Erros

### Tipos de Erro
- **Linha não detectada**: Parar e tentar recuperar
- **Interseção não encontrada**: Timeout e retorno
- **QR code errado**: Continuar procurando
- **Falha de movimento**: Retry com backoff
- **Perda de comunicação**: Modo degradado

### Estratégias de Recuperação
- **Retry automático**: Até 3 tentativas
- **Modo manual**: Intervenção do operador
- **Retorno à base**: Em caso de falha crítica
- **Logging detalhado**: Para diagnóstico

## 📊 Monitoramento e Logs

### Métricas Principais
- **Taxa de detecção de linha**: % de frames com linha detectada
- **Precisão de QR**: % de códigos lidos corretamente
- **Tempo de missão**: Duração total
- **Distância percorrida**: Baseada em odometria
- **Eficiência de navegação**: Distância ótima vs real

### Logs Estruturados
```python
logger.info("Linha detectada", extra={
    'center': line_center,
    'width': line_width,
    'confidence': confidence,
    'steering_correction': correction
})

logger.info("Interseção encontrada", extra={
    'subcorredor': target_subcorredor,
    'qr_detectado': qr_code,
    'tempo_busca': elapsed_time
})
```

## 🔄 Comunicação com PC

### API Endpoints
- `POST /execute_command`: Comando de missão
- `GET /status`: Status atual do AGV
- `POST /status`: Atualização de status

### Protocolo de Comando
```json
{
  "type": "start_mission",
  "data": {
    "order_id": 123,
    "items": ["TAG0001", "TAG0002"],
    "subcorredores": ["01", "02"]
  }
}
```

## 🚀 Próximos Passos

### Melhorias Planejadas
- **Mapeamento SLAM**: Navegação mais precisa
- **Otimização de rota**: Algoritmos avançados
- **Detecção de obstáculos**: Evitar colisões
- **Interface HMI**: Controle em tempo real
- **Machine Learning**: Detecção robusta de linha

### Integração com Braço Robótico
- **Sequenciamento**: Coordenação entre navegação e coleta
- **Posicionamento preciso**: Alinhamento com prateleiras
- **Feedback visual**: Confirmação de coleta
- **Gestão de carga**: Controle de peso e estabilidade

Este sistema fornece uma base sólida para navegação autônoma do AGV, com detecção robusta de linha preta e integração completa com QR codes para localização precisa.