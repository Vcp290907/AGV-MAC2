# AGV Raspberry - Sistema de Controle

Sistema embarcado para controle físico do carrinho AGV.

## 🤖 Componentes

- **Controle**: Lógica de navegação e execução
- **Hardware**: Interface com ESP32, motores e sensores  
- **Camera**: OpenCV para visão computacional
- **Comunicação**: API local para receber comandos

## 🚀 Execução

```bash
python main.py
```

## 📡 API Local

O Raspberry expõe uma API simples em `http://IP_RASPBERRY:8080`:

### Endpoints:
- `POST /executar` - Executa comando recebido
- `GET /status` - Retorna status atual
- `GET /camera` - Stream da câmera

## 🔧 Hardware

### Conexões:
- **ESP32**: Comunicação serial (USB/UART)
- **Câmera**: Interface CSI do Raspberry Pi
- **GPIO**: Controle direto de sensores

### Funcionalidades:
- Navegação autônoma
- Detecção de obstáculos
- Controle de velocidade
- Leitura de códigos/tags
