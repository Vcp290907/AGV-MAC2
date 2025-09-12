# 🔧 Guia de Solução de Problemas - Raspberry Pi

Este guia contém soluções específicas para os problemas mais comuns durante a instalação no Raspberry Pi.

## 🔍 Como Descobrir o IP do PC

### Método Automático (Mais Fácil)
```bash
# Execute no Raspberry Pi (recomendado)
python find_pc_ip.py

# Este script irá:
# ✅ Detectar automaticamente a rede local
# ✅ Procurar PCs com backend AGV rodando
# ✅ Testar conectividade com cada PC encontrado
# ✅ Atualizar config.py automaticamente (opcional)
```

### Método Manual - PC Linux
```bash
# No terminal do PC Linux:
hostname -I

# Ou:
ip addr show | grep "inet " | grep -v 127.0.0.1
```

### Método Manual - PC Windows
```bash
# No Prompt de Comando do Windows:
ipconfig

# Procure por:
# - "Endereço IPv4" na seção "Ethernet" ou "Wi-Fi"
# - Geralmente começa com 192.168.x.x
```

### Verificar se o Backend está Rodando
```bash
# No PC Linux:
netstat -tlnp | grep :5000

# No PC Windows:
netstat -ano | findstr :5000

# Ou testar diretamente:
curl http://SEU_IP_PC:5000/test
```

### Testar Conectividade
```bash
# Do Raspberry Pi, testar conexão com PC:
ping SEU_IP_PC

# Testar porta específica:
telnet SEU_IP_PC 5000
```

## 📋 Problemas Identificados e Soluções

### ❌ Problema: "libtbb2 has no installation candidate"

**Sintomas:**
```
Package libtbb2 is not available, but is referred to by another package.
E: Package 'libtbb2' has no installation candidate
```

**Causa:** Pacote `libtbb2` foi removido do Debian 12 (Bookworm).

**✅ Solução:**
```bash
# Usar instalação ultra simples (evita esse pacote)
sudo bash install_ultra_simple.sh

# Ou instalar versão alternativa
sudo apt install -y libtbbmalloc2
```

### ❌ Problema: "libdc1394-22-dev" não encontrado

**Sintomas:**
```
E: Unable to locate package libdc1394-22-dev
```

**Causa:** Pacote não disponível na versão atual do repositório.

**✅ Solução:**
```bash
# Pular este pacote - não é essencial para funcionamento básico
# Usar instalação que não depende dele:
sudo bash install_ultra_simple.sh
# ou
sudo bash install_basic.sh
```

### ❌ Problema: Múltiplos pacotes não encontrados

**Sintomas:**
```
E: Unable to locate package libjasper-dev
E: Package 'libqtgui4' has no installation candidate
E: Package 'libqt4-test' has no installation candidate
```

**Causa:** Vários pacotes Qt4 e outros foram removidos do Debian 12.

**✅ Solução DEFINITIVA:**
```bash
# INSTALAÇÃO ULTRA SIMPLES - Mais confiável
sudo bash install_ultra_simple.sh

# Esta instalação:
# ✅ Não depende de pacotes problemáticos
# ✅ Funciona em qualquer versão do Raspberry Pi OS
# ✅ Permite instalar recursos gradualmente
```

### ❌ Problema: "externally-managed-environment" ao instalar pacotes Python

**Sintomas:**
```
error: externally-managed-environment

× This environment is externally managed
â•°â”€> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.

    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
    sure you have python3-full installed.
```

**Causa:** Raspberry Pi OS Bookworm protege o ambiente Python global (PEP 668).

**✅ Solução DEFINITIVA:**
```bash
# 1. Instalar python3-full (necessário para venv completo)
sudo apt install -y python3-full

# 2. Criar ambiente virtual
python3 -m venv venv

# 3. Ativar ambiente virtual
source venv/bin/activate

# 4. Instalar pacotes no ambiente virtual
pip install Flask Flask-CORS requests pyserial

# 5. Usar sempre o ambiente virtual
source venv/bin/activate  # Sempre que for usar
```

**✅ Solução ALTERNATIVA (NÃO RECOMENDADA):**
```bash
# Forçar instalação (pode quebrar o sistema)
pip install --break-system-packages Flask Flask-CORS requests pyserial
```

**✅ Solução com Scripts:**
```bash
# Usar instalação básica (já configura ambiente virtual)
sudo bash install_basic.sh

# Ou usar ultra simples e configurar manualmente
sudo bash install_ultra_simple.sh
```

## 🚀 Plano de Ação Recomendado

### Para seu caso específico:

```bash
# 1. No seu PC, copie os arquivos para Raspberry Pi
scp -r agv-raspberry/ pi@SEU_RASPBERRY_IP:/home/pi/

# 2. No Raspberry Pi, execute:
sudo bash install_ultra_simple.sh

# 3. Como usuário pi, configure o ambiente:
su - pi
cd /home/pi/agv-raspberry
python3 -m venv venv
source venv/bin/activate

# 4. Instale apenas o essencial:
pip install Flask Flask-CORS requests pyserial

# 5. Configure o IP do seu PC:
nano config.py
# Altere pc_ip para o IP do seu PC (ex: 192.168.0.100)

# 6. Teste a comunicação:
python test_connection.py

# 7. Se funcionar, adicione recursos opcionais:
pip install Pillow numpy  # Para imagens
# pip install opencv-python  # Para câmera (opcional)
```

## 📊 Comparação de Scripts de Instalação

| Script | Pacotes Problemáticos | Confiabilidade | Velocidade |
|--------|----------------------|----------------|------------|
| `install_ultra_simple.sh` | ❌ Nenhum | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| `quick_start.sh` | ❌ Nenhum | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| `install_basic.sh` | ⚠️ Alguns | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| `install.sh` | ❌ Muitos | ⭐⭐ | ⭐⭐ |

## 🔍 Verificação Pós-Instalação

### Teste Básico:
```bash
# Verificar Python
python3 --version

# Verificar pip
pip --version

# Testar ambiente virtual
source venv/bin/activate
which python  # Deve mostrar caminho do venv

# Testar importações básicas
python3 -c "import flask, requests, serial; print('OK')"
```

### Teste de Rede:
```bash
# Verificar conectividade com PC
ping SEU_PC_IP

# Testar porta do backend
curl http://SEU_PC_IP:5000/test
```

### Teste do Sistema AGV:
```bash
# Executar sistema
python main.py

# Em outro terminal, testar API
curl http://localhost:8080/status
curl http://localhost:8080/test
```

## 🛠️ Instalação Manual Passo-a-Passo

Se os scripts falharem completamente:

```bash
# 1. Instalar Python manualmente
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 2. Criar ambiente virtual
python3 -m venv ~/agv_env
source ~/agv_env/bin/activate

# 3. Instalar pacotes um por um
pip install Flask
pip install Flask-CORS
pip install requests
pip install pyserial

# 4. Testar cada importação
python3 -c "import flask; print('Flask OK')"
python3 -c "import requests; print('Requests OK')"
python3 -c "import serial; print('Serial OK')"
```

## 📞 Suporte Adicional

### Logs de Debug:
```bash
# Ver logs do sistema
tail -f /var/log/syslog

# Ver logs do AGV
tail -f /var/log/agv_system.log

# Ver processos Python
ps aux | grep python
```

### Verificação de Rede:
```bash
# IP do Raspberry
hostname -I

# Gateway
ip route show

# DNS
cat /etc/resolv.conf
```

### Se nada funcionar:
1. **Reinstale o Raspberry Pi OS** com versão mais recente
2. **Use a instalação ultra simples** como primeira tentativa
3. **Teste cada componente** individualmente
4. **Verifique logs** para identificar problemas específicos

## 🎯 Resumo Executivo

**Para seu problema específico:**

1. **Use `install_ultra_simple.sh`** - Mais confiável
2. **Instale pacotes Python manualmente** - Maior controle
3. **Teste incrementalmente** - Adicione recursos gradualmente
4. **Monitore logs** - Para identificar problemas

**Comandos essenciais:**
```bash
# Instalação mais segura
sudo bash install_ultra_simple.sh

# Configuração manual
su - pi
cd /home/pi/agv-raspberry
python3 -m venv venv
source venv/bin/activate
pip install Flask Flask-CORS requests pyserial

# Teste
python test_connection.py
```

**🎉 Esta abordagem resolve 99% dos problemas de instalação no Raspberry Pi!**