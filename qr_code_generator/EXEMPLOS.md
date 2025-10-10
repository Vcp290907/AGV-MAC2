# Exemplos de uso do Gerador de QR Codes

## 🚀 Instalação rápida

```bash
pip install -r requirements.txt
```

## 📱 Exemplos práticos

### 1. URL simples
```bash
python qr_rapido.py "https://www.google.com"
# Gera: qr_https:__www.google.com.svg
```

### 2. Texto personalizado
```bash
python qr_rapido.py "Bem-vindo ao meu projeto!"
# Gera: qr_Bem-vindo_ao_meu_projeto!.svg
```

### 3. Dados JSON
```bash
python qr_rapido.py '{"nome": "João Silva", "cargo": "Desenvolvedor", "empresa": "Tech Corp"}'
# Gera: qr_{"nome":_"João_Silva",_"cargo":_"Desenvolvedor",_"empresa":_"Tech_Corp"}.svg
```

### 4. Número de telefone
```bash
python qr_rapido.py "tel:+5511999999999"
# Gera: qr_tel:+5511999999999.svg
```

### 5. Email
```bash
python qr_rapido.py "mailto:contato@empresa.com"
# Gera: qr_mailto:contato@empresa.com.svg
```

### 6. Localização GPS
```bash
python qr_rapido.py "geo:-23.550520,-46.633308"
# Gera: qr_geo:-23.550520,-46.633308.svg
```

## 🎨 Usando a versão avançada

Para personalizar o QR code:

```bash
python gerador_qr_avancado.py
```

E siga as instruções para:
- Escolher nível de correção de erro
- Definir tamanho dos módulos
- Configurar borda
- Etc.

## 📂 Arquivos gerados

Todos os arquivos SVG são salvos na pasta **`qrcodes_gerados/`** e podem ser:
- Abertos em qualquer navegador web
- Editados em softwares como Inkscape
- Impressos em qualquer tamanho
- Compartilhados digitalmente

## 💡 Dicas

- **Nomes longos**: São automaticamente truncados para o nome do arquivo
- **Caracteres especiais**: São convertidos para `_` no nome do arquivo
- **Arquivos duplicados**: Recebem numeração automática (_1, _2, etc.)
- **Pasta organizada**: Todos os QR codes ficam na pasta `qrcodes_gerados/`
- **Formato SVG**: Vetorial, pode ser redimensionado sem perder qualidade