# AGV Mobile App

Aplicativo móvel React Native para controle e monitoramento do sistema AGV (Automated Guided Vehicle).

## 🚀 Funcionalidades

- **Login Seguro**: Autenticação integrada com o backend Flask
- **Dashboard**: Visão geral do sistema e estatísticas
- **Criação de Pedidos**: Seleção de itens e dispositivos AGV
- **Monitoramento em Tempo Real**: Status dos AGVs e pedidos
- **Interface Intuitiva**: Design moderno com Material Design

## 📱 Telas

### 1. Login Screen
- Autenticação de usuário
- Conexão com backend Flask
- Armazenamento seguro de sessão

### 2. Dashboard Screen
- Visão geral do sistema
- Estatísticas rápidas
- Navegação para outras funcionalidades

### 3. Order Screen (Pedidos)
- Seleção de itens disponíveis
- Escolha de dispositivo AGV
- Criação de pedidos de coleta
- Histórico de pedidos

### 4. Status Screen
- Monitoramento de AGVs
- Status de bateria e localização
- Lista de pedidos ativos por dispositivo

## 🛠️ Tecnologias

- **React Native**: Framework para desenvolvimento mobile
- **TypeScript**: Tipagem estática para melhor desenvolvimento
- **React Navigation**: Navegação entre telas
- **React Native Paper**: Componentes Material Design
- **AsyncStorage**: Armazenamento local de dados
- **Socket.io**: Comunicação em tempo real (futuro)

## 📦 Dependências

```json
{
  "@react-navigation/native": "^6.1.9",
  "@react-navigation/native-stack": "^6.9.17",
  "react-native-safe-area-context": "^4.7.4",
  "react-native-screens": "^3.27.0",
  "react-native-paper": "^5.11.3",
  "@react-native-async-storage/async-storage": "^1.19.5",
  "socket.io-client": "^4.7.4"
}
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- Node.js >= 16
- npm ou yarn
- React Native CLI
- Android Studio (para Android) ou Xcode (para iOS)

### Passos de Instalação

1. **Instalar dependências:**
   ```bash
   cd agv-mobile
   npm install
   ```

2. **Instalar dependências do iOS (macOS apenas):**
   ```bash
   cd ios && pod install
   ```

3. **Configurar IP do servidor:**
   - Edite os arquivos das telas para apontar para o IP correto do seu servidor Flask
   - Padrão: `http://192.168.1.100:5000`

### Executando o App

**Android:**
```bash
npm run android
```

**iOS:**
```bash
npm run ios
```

**Desenvolvimento:**
```bash
npm start
```

## 🔧 Configuração

### Conexão com Backend

O app se conecta ao backend Flask através de HTTP. Configure o IP correto nos arquivos:

- `src/screens/LoginScreen.tsx`
- `src/screens/DashboardScreen.tsx`
- `src/screens/OrderScreen.tsx`
- `src/screens/StatusScreen.tsx`

```typescript
const API_BASE_URL = 'http://SEU_IP_AQUI:5000';
```

### Credenciais de Teste

- **Usuário:** 123 / **Senha:** 123 (Gerente)
- **Usuário:** joao / **Senha:** 123456 (Funcionário)

## 📱 Funcionalidades Planejadas

- [ ] **QR Code Scanning**: Leitura de códigos QR para identificação de itens
- [ ] **WebSocket Integration**: Atualizações em tempo real
- [ ] **Offline Mode**: Funcionamento básico sem conexão
- [ ] **Push Notifications**: Alertas de status de pedidos
- [ ] **GPS Integration**: Rastreamento de localização dos AGVs

## 🏗️ Arquitetura

```
agv-mobile/
├── src/
│   ├── screens/          # Telas do app
│   │   ├── LoginScreen.tsx
│   │   ├── DashboardScreen.tsx
│   │   ├── OrderScreen.tsx
│   │   └── StatusScreen.tsx
│   ├── theme/            # Tema e estilos
│   │   └── theme.ts
│   └── services/         # Serviços (futuro)
├── App.tsx               # App principal
├── package.json          # Dependências
└── tsconfig.json         # Configuração TypeScript
```

## 🔒 Segurança

- Autenticação JWT via backend
- Armazenamento seguro de tokens
- Validação de entrada de dados
- Comunicação HTTPS (recomendado)

## 📊 Monitoramento

O app se integra com o sistema de monitoramento do backend para:

- Status em tempo real dos AGVs
- Atualização automática de pedidos
- Alertas de bateria baixa
- Logs de operações

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é parte do sistema AGV e segue a mesma licença do projeto principal.

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o desenvolvimento:

- Verifique os logs do console para erros
- Confirme a conectividade com o backend
- Teste com as credenciais de demonstração
- Consulte a documentação do backend Flask

---

**Nota:** Este app foi desenvolvido para funcionar integrado com o sistema AGV backend. Certifique-se de que o servidor Flask esteja rodando antes de usar o app móvel.