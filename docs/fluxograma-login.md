# Fluxograma do Sistema de Login - AGV Dashboard

## Descrição
Este fluxograma representa o fluxo completo de autenticação entre o front-end (React) e o back-end (Flask) do sistema AGV.

## Fluxograma em Mermaid

```mermaid
flowchart TD
    A[Usuario acessa a pagina de login] --> B[Frontend: Login.jsx carrega]
    B --> C[Usuario preenche credenciais]
    C --> D{Campos obrigatorios preenchidos?}
    
    D -->|Nao| E[Frontend: Exibe erro de validacao]
    E --> C
    
    D -->|Sim| F[Frontend: Envia POST para /login]
    F --> G[Loading = true]
    G --> H[HTTP Request para Backend]
    
    H --> I[Backend: auth.py recebe requisicao]
    I --> J[Backend: Extrai username e password]
    J --> K{Campos vazios?}
    
    K -->|Sim| L[Retorna erro 400: Campos obrigatorios]
    K -->|Nao| M[Chama verificar_usuario]
    
    M --> N[database.py: Conecta ao SQLite]
    N --> O[Criptografa senha com SHA256]
    O --> P[Busca usuario no banco]
    P --> Q{Usuario encontrado e ativo?}
    
    Q -->|Nao| R[Retorna erro 401: Credenciais invalidas]
    Q -->|Sim| S[Retorna sucesso + dados do usuario]
    
    L --> T[Frontend: Recebe resposta]
    R --> T
    S --> T
    
    T --> U{Response.success?}
    
    U -->|Nao| V[Frontend: Exibe mensagem de erro]
    V --> W[Loading = false]
    W --> C
    
    U -->|Sim| X[Frontend: Salva dados no localStorage]
    X --> Y[Loading = false]
    Y --> Z[Frontend: Chama onLogin]
    Z --> AA[Redireciona para Dashboard]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style I fill:#fff3e0
    style N fill:#e8f5e8
    style AA fill:#e8f5e8
    style V fill:#ffebee
    style L fill:#ffebee
    style R fill:#ffebee
```

## Componentes do Fluxo

### 1. Frontend (React)
- **Arquivo**: `agv-web/frontend/src/pages/Login.jsx`
- **Responsabilidades**:
  - Capturar credenciais do usuário
  - Validar campos obrigatórios
  - Enviar requisição HTTP para backend
  - Gerenciar estados (loading, erro)
  - Salvar dados do usuário autenticado
  - Redirecionar para dashboard

### 2. Backend (Flask)
- **Arquivo**: `agv-web/backend/api/auth.py`
- **Endpoint**: `POST /login`
- **Responsabilidades**:
  - Receber e validar dados da requisição
  - Chamar função de verificação de usuário
  - Retornar resposta apropriada

### 3. Banco de Dados (SQLite)
- **Arquivo**: `agv-web/backend/database.py`
- **Função**: `verificar_usuario()`
- **Responsabilidades**:
  - Criptografar senha com SHA256
  - Consultar usuário no banco
  - Verificar se está ativo
  - Retornar dados do usuário

## Estados de Resposta

### ✅ Sucesso (200)
```json
{
  "success": true,
  "message": "Login realizado com sucesso",
  "usuario": {
    "id": 1,
    "nome": "João Silva",
    "username": "joao",
    "perfil": "funcionario"
  }
}
```

### ❌ Campos Obrigatórios (400)
```json
{
  "success": false,
  "message": "Username e senha são obrigatórios"
}
```

### ❌ Credenciais Inválidas (401)
```json
{
  "success": false,
  "message": "Credenciais inválidas"
}
```

## Fluxo de Dados

1. **Entrada**: Username e Password
2. **Processamento**: Validação → Criptografia → Consulta DB
3. **Saída**: Dados do usuário ou mensagem de erro

## Segurança

- ✅ Senhas criptografadas com SHA256
- ✅ Validação de campos obrigatórios
- ✅ Verificação de usuário ativo
- ✅ Tratamento de erros padronizado
- ✅ Estados de loading no frontend

## URLs e Endpoints

- **Frontend**: `http://localhost:3000/login`
- **Backend API**: `http://localhost:5000/login`
- **Método**: POST
- **Content-Type**: application/json