# 🎯 Gerador de QR Codes - SVG

Um programa simples em P### 4. Demonstração das Diferenças

```bash
python demonstracao.py
```

**Gera todos os 3 tipos para comparação visual:**
- `demo_padrao.svg` - Módulos separados
- `demo_otimizado.svg` - Otimizado para CAD/CAM
- `demo_visual_solido.svg` - Blocos contínuos (⚠️ não legível)

### 5. Verificar Leitura dos QR Codes

```bash
python teste_leitura_qr.py
```

**Testa se os QR codes podem ser lidos corretamente**

### 6. Gerenciar QR Codesgerar QR codes a partir de texto e exportar em formato ## 🎯 Caract## 🎯 Características do QR Code

- **Formato**: SVG (Scalable Vector Graphics) **otimizado para CAD/CAM**
- **Renderização**: Usa `<path>` com blocos conectados (compatível com Fusion 360, AutoCAD, etc.)
- **Tipos disponíveis**:
  - **Padrão**: Módulos separados (melhor para leitores de QR)
  - **Sólido**: Blocos conectados (melhor para CAD/CAM e usinagem)
- **Correção de erro**: Configurável (L/M/Q/H)
- **Tamanho**: Automático baseado no conteúdo
- **Borda**: Configurável (padrão: 4 módulos)
- **Pasta de destino**: `qrcodes_gerados/` (criada automaticamente)
- **Vetorial**: Pode ser redimensionado sem perder qualidadearacterísticas do QR Coderísticas do QR Code

- **Formato**: SVG (Scalable Vector Graphics) **otimizado para CAD/CAM**
- **Renderização**: Usa `<path>` em vez de retângulos individuais (compatível com Fusion 360, AutoCAD, etc.)
- **Correção de erro**: Configurável (L/M/Q/H)
- **Tamanho**: Automático baseado no conteúdo
- **Borda**: Configurável (padrão: 4 módulos)
- **Pasta de destino**: `qrcodes_gerados/` (criada automaticamente)
- **Vetorial**: Pode ser redimensionado sem perder qualidade
## ✨ Funcionalidades

- ✅ Geração de QR codes a partir de qualquer texto
- ✅ Exportação em formato SVG (vetorial, escalável)
- ✅ Interface interativa via terminal
- ✅ Nomes de arquivo automáticos e únicos
- ✅ Tratamento de erros
- 🎨 **Versão avançada** com personalização completa

## 🚀 Como Usar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Versão Simples

```bash
python gerador_qr.py
```

### 3. Versão de Linha de Comando (mais rápida)

```bash
python qr_rapido.py "Seu texto aqui"
```

**Exemplos:**
```bash
python qr_rapido.py "https://www.google.com"
python qr_rapido.py "Olá Mundo!"
python qr_rapido.py '{"nome": "João", "idade": 30}'
```

### 4. Testar Diferença Entre Tipos

```bash
python teste_tipos.py
```

**Gera ambos os tipos para comparação:**
- `qr_TESTE_padrao.svg` - Módulos separados
- `qr_TESTE_solido_final.svg` - Blocos conectados

### 5. Gerenciar QR Codes

```bash
python gerenciar_qr.py
```

**Funcionalidades:**
- 📋 Listar todos os QR codes gerados
- 📊 Ver estatísticas (quantidade, espaço ocupado, datas)
- 🗑️ Limpar QR codes antigos (com confirmação)

### 4. Usar o programa

**Versão Simples:**
```
🎯 GERADOR DE QR CODES - SVG
========================================

📝 Digite o texto para gerar o QR Code:
(ou 'sair' para encerrar)
> Olá Mundo!
✅ QR Code gerado com sucesso!
📁 Arquivo salvo: qr_Olá_Mundo!.svg
📝 Texto codificado: Olá Mundo!
🎉 QR Code pronto! Você pode abrir o arquivo qr_Olá_Mundo!.svg
```

**Versão Avançada:**
```
🎯 GERADOR AVANÇADO DE QR CODES
==================================================

📝 Digite o texto para o QR Code:
(ou 'sair' para encerrar, 'menu' para opções)
> https://www.google.com
```

## 🎨 Personalização (Versão Avançada)

### Opções Disponíveis:

- **Versão**: Tamanho do QR code (1-40, automático recomendado)
- **Correção de erro**:
  - `L`: 7% (padrão, menor tamanho)
  - `M`: 15% (bom equilíbrio)
  - `Q`: 25% (alta correção)
  - `H`: 30% (máxima correção, maior tamanho)
- **Tamanho do módulo**: Pixels por quadrado do QR
- **Borda**: Margem em módulos ao redor do código

### Exemplo de Personalização:

```
🔧 Usar configurações padrão? (s/n)
> n

🎨 CONFIGURAÇÕES PERSONALIZADAS:
Versão (1-40, Enter=automático):
> 
Correção de erro (L=7%, M=15%, Q=25%, H=30%) [L]:
> H
Tamanho do módulo (pixels) [10]:
> 15
Tamanho da borda (módulos) [4]:
> 6
```

## 📋 Exemplos de uso

### Texto simples
```
> https://www.google.com
```

### Texto longo
```
> Este é um exemplo de texto longo que será codificado no QR code
```

### Dados estruturados
```
> {"nome": "João", "email": "joao@email.com", "telefone": "11999999999"}
```

### URLs
```
> https://github.com/seu-usuario/seu-projeto
```

## � Características do QR Code

- **Formato**: SVG (Scalable Vector Graphics)
- **Correção de erro**: Configurável (L/M/Q/H)
- **Tamanho**: Automático baseado no conteúdo
- **Borda**: Configurável (padrão: 4 módulos)
- **Vetorial**: Pode ser redimensionado sem perder qualidade

## 📁 Arquivos gerados

Todos os QR codes são salvos automaticamente na pasta **`qrcodes_gerados/`** com nomes como:
- `qrcodes_gerados/qr_Texto_digitado.svg`
- `qrcodes_gerados/qr_Texto_digitado_1.svg` (se já existir)
- `qrcodes_gerados/qr_Texto_digitado_2.svg` (se já existirem outros)

## 🛠️ Personalização Avançada

Você pode modificar o código fonte para:
- Alterar cores do QR code
- Adicionar logos ou imagens
- Mudar formatos de saída
- Integrar com outras aplicações

## 📚 Dependências

- `qrcode[pil]` - Biblioteca principal para geração de QR codes
- `Pillow` - Para suporte a imagens (incluído no qrcode[pil])

## 💡 Dicas

- **SVG é vetorial**: Pode ser redimensionado sem perder qualidade
- **Compatibilidade**: Funciona em qualquer software que suporte SVG
- **Leitura**: Use qualquer app de leitura de QR code no celular
- **Correção H**: Ideal para ambientes com possível interferência
- **Versão automática**: Funciona na maioria dos casos

## 🔧 Compatibilidade CAD/CAM

Os QR codes gerados são **100% compatíveis** com softwares CAD/CAM como:
- **Fusion 360**
- **AutoCAD**
- **SolidWorks**
- **Inventor**
- **Outros softwares que suportam SVG vetorial**

### Por que funciona?
- Usa `SvgPathImage` em vez de `SvgImage`
- Gera path SVG otimizado mantendo funcionalidade de leitura
- Coordenadas absolutas para melhor precisão
- Compatível com Fusion 360, AutoCAD, SolidWorks

### Tipo Sólido vs Padrão
- **Padrão**: Módulos separados (melhor para leitura por apps de celular)
- **Otimizado**: Módulos individuais (melhor para CAD/CAM, mantém leitura)
- **Visual Sólido**: Blocos contínuos conectados (aparência sólida ⚠️ **NÃO FUNCIONA** para leitura)

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'qrcode'"
```bash
pip install -r requirements.txt
```

### QR Code muito pequeno
- Aumente o "tamanho do módulo" na versão avançada
- Use versão maior se necessário

### Arquivo não abre
- SVG pode ser aberto em navegadores (Chrome, Firefox, Edge)
- Use editores vetoriais como Inkscape

---

**Criado com ❤️ para facilitar a geração de QR codes!**