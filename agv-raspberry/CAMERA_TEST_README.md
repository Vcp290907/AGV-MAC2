# 🧪 Teste de Câmera CSI - Sistema AGV

Este guia ajuda você a testar e configurar a câmera CSI (cabo flat) no s### Diagnóstico Detalhado Chinesa 🔬 **(ANÁLISE PROFUNDA)**
```bash
bash diagnose_chinese_csi.sh
```

Script específico para diagnosticar problemas em câmeras chinesas CSI:
- ✅ Verificação detalhada de dispositivos V4L2
- ✅ Testes de captura com diferentes formatos/resoluções
- ✅ Análise de drivers e módulos do kernel
- ✅ Verificação de logs do sistema
- ✅ Diagnóstico de problemas de hardware

### Verificação Rápida de Sinal 📡 **(TESTE IMEDIATO)**
```bash
bash check_csi_signal.sh
```

Verificação ultra-rápida se há sinal no barramento CSI:
- ✅ Testa conectividade CSI em tempo real
- ✅ Mostra logs de detecção de câmera
- ✅ Diagnóstico em segundos

### Guia de Emergência 🚨 **(CÂMERA NÃO DETECTADA)**
```bash
# Leia: CSI_CHINESE_EMERGENCY.md
```

Guia específico para quando "csi2_ch0 node link is not enabled":
- ✅ Diagnóstico do problema físico
- ✅ Soluções passo a passo
- ✅ Verificações de hardwarey Pi 5 para o sistema AGV.

## 📋 Pré-requisitos

- Raspberry Pi 5 com Raspberry Pi OS (64-bit)
- **Câmera CSI oficial** conectada via cabo flat
- Python 3.9+ instalado

## 🔌 Conexão da Câmera CSI

### Verificar Conexão Física
1. Certifique-se de que o cabo flat está **firmemente conectado** nos dois conectores
2. O conector azul da câmera deve estar voltado para o cabo USB
3. Não force a conexão - ela deve entrar suavemente

### Tipos de Câmera Suportados

#### 🏷️ **Câmera Oficial Raspberry Pi**
- Modelo: Raspberry Pi Camera Module 3
- Compatibilidade: Total com libcamera
- Detecção: `vcgencmd get_camera` mostra `detected=1`

#### 🇨🇳 **Câmera CSI Chinesa (Genérica)**
- Modelos: ArduCam, Waveshare, câmeras OV2710/OV2715, etc.
- Compatibilidade: V4L2 direto (não usa libcamera)
- Detecção: Aparece como `/dev/video0`, `/dev/video1`, etc.
- **IMPORTANTE**: `vcgencmd get_camera` **sempre** mostra `detected=0`

### Habilitar no Sistema
```bash
# Executar configuração
sudo raspi-config

# Navegar: Interfacing Options -> Camera -> Enable
# Depois: Finish -> Reboot
```

### Verificar Detecção
```bash
# Para câmera oficial
vcgencmd get_camera

# Deve mostrar: detected=1

# Para câmera chinesa - verificar V4L2
v4l2-ctl --list-devices
```

## 🚀 Instalação

### 1. Verificar Conexão CSI
```bash
bash check_csi_connection.sh
```

### 2. Instalar Dependências
```bash
bash install_camera_deps.sh
```

### 3. Configurar Permissões
```bash
# Adicionar usuário ao grupo video
sudo usermod -a -G video $USER

# Logout/login ou reboot
sudo reboot
```

### 2. Configurar Câmera CSI

Se estiver usando a câmera CSI oficial:

```bash
# Habilitar câmera via raspi-config
sudo raspi-config
# Navegue: Interfacing Options -> Camera -> Enable

# Reiniciar
sudo reboot
```

## 🧪 Testes

### Teste Básico (Todas as Câmeras)
```bash
python3 test_camera.py
```

## 🧪 Testes

### Verificação Ultra Rápida 🔍 **(COMECE AQUI)**
```bash
python3 check_cameras.py
```

Verifica rapidamente quais índices de câmera estão disponíveis:
- ✅ Testa índices 0-9 em segundos
- ✅ Mostra resolução de cada câmera
- ✅ Identifica câmeras funcionando

### Foto Simples 📷 **(TESTE BÁSICO)**
```bash
python3 take_simple_photo.py
```

Teste mais simples possível - apenas abre câmera e tira uma foto:
- ✅ Abre câmera no índice 0
- ✅ Tira uma foto
- ✅ Salva como `foto_simples.jpg`
- ✅ Fecha câmera

### Teste Específico CSI ⭐ **(RECOMENDADO)**
```bash
python3 test_csi_camera.py
```

Este script testa especificamente a câmera CSI com:
- ✅ libcamera (ferramentas nativas)
- ✅ OpenCV com diferentes backends
- ✅ GStreamer pipelines
- ✅ Cria script de teste contínuo

### Teste Específico CSI Chinesa 🇨🇳 **(PARA CÂMERAS CHINESAS)**
```bash
python3 test_chinese_csi_camera.py
```

Este script testa câmeras CSI chinesas que **não funcionam com libcamera**:
- ✅ OpenCV com V4L2 direto
- ✅ v4l2-ctl para controle direto
- ✅ GStreamer sem libcamerasrc
- ✅ Verificação de formatos suportados
- ✅ Cria script de teste contínuo

### Diagnóstico Detalhado Chinesa 🔬 **(ANÁLISE PROFUNDA)**
```bash
bash diagnose_chinese_csi.sh
```

Script específico para diagnosticar problemas em câmeras chinesas CSI:
- ✅ Verificação detalhada de dispositivos V4L2
- ✅ Testes de captura com diferentes formatos
- ✅ Análise de drivers e módulos do kernel
- ✅ Verificação de logs do sistema
- ✅ Diagnóstico de problemas de hardware

### Teste de QR Codes
```bash
python3 test_qr_codes.py
```

### Teste Contínuo
```bash
python3 test_csi_continuous.py
```

### Executar Todos os Testes
```bash
bash run_all_camera_tests.sh
```

## � SE OS TESTES FALHARAM - SOLUÇÃO RÁPIDA

Se você viu esta saída:
```
❌ libcamera preview: FALHA
❌ libcamera capture: FALHA
❌ OpenCV CSI: FALHA
❌ GStreamer: FALHA
```

### 🔍 Diagnóstico Automático
```bash
bash diagnose_csi_camera.sh
```

### 🛠️ Correção Automática
```bash
bash fix_csi_camera.sh
```

### 📋 Verificação Manual
```bash
# 1. Verificar detecção
vcgencmd get_camera

# 2. Habilitar câmera
sudo raspi-config  # Interfacing Options -> Camera -> Enable

# 3. Reiniciar
sudo reboot

# 4. Testar novamente
python3 test_csi_camera.py
```

**Para detalhes completos:** Ver [CSI_TROUBLESHOOTING.md](CSI_TROUBLESHOOTING.md)

## �🔧 Solução de Problemas

## 🔧 Solução de Problemas

### Câmera CSI não Detectada

#### Verificar Conexão Física
```bash
# Verificar detecção
vcgencmd get_camera

# Deve mostrar: detected=1
# Se mostrar detected=0, verifique:
# 1. Cabo flat conectado corretamente
# 2. Conector não danificado
# 3. Câmera compatível com Pi 5
```

#### Habilitar no raspi-config
```bash
sudo raspi-config
# Interfacing Options -> Camera -> Enable
# Finish -> Reboot
```

#### Verificar Configuração
```bash
# Verificar config.txt
cat /boot/firmware/config.txt | grep camera

# Se não encontrar, adicionar manualmente:
echo "camera_auto_detect=1" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

### libcamera não Funciona

```bash
# Verificar instalação
libcamera-hello --version

# Teste básico
libcamera-hello -t 2000

# Com preview (se display disponível)
libcamera-hello --qt-preview -t 5000
```

### OpenCV não Encontra Câmera

```bash
# Testar diferentes índices
python3 -c "
import cv2
for i in [0, 1, 2, 10, 11, 12]:
    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
    if cap.isOpened():
        print(f'CSI encontrada no índice {i}')
        cap.release()
        break
    cap.release()
"
```

### Problemas de Permissão

```bash
# Verificar grupo
groups $USER

# Adicionar ao grupo video
sudo usermod -a -G video $USER

# Logout e login novamente, ou:
sudo reboot
```

### GStreamer Falha

```bash
# Testar pipeline básico
gst-launch-1.0 libcamerasrc ! videoconvert ! autovideosink

# Com resolução específica
gst-launch-1.0 libcamerasrc ! video/x-raw,width=640,height=480 ! videoconvert ! autovideosink
```

## 📊 Resultados Esperados

### Teste CSI (test_csi_camera.py) ⭐ **(RESULTADO ESPERADO)**
```
🎥 TESTE ESPECÍFICO DE CÂMERA CSI - RASPBERRY PI 5
🔍 Verificando libcamera...
✅ libcamera encontrado

📷 Testando preview com libcamera...
   Iniciando preview (5 segundos)...
✅ Preview da câmera CSI funcionou!

📸 Testando captura de imagem com libcamera...
✅ Imagem capturada: teste_csi.jpg (245760 bytes)

🐍 Testando câmera CSI com OpenCV...
   Testando backend V4L2...
   ✅ CSI funcionando com V4L2 (índice 0)
      📐 Resolução: 640x480
      💾 Frame salvo: teste_opencv_csi.jpg

📊 RESUMO DOS TESTES CSI
libcamera preview:  ✅ OK
libcamera capture:  ✅ OK
OpenCV CSI:         ✅ OK
GStreamer:          ❌ FALHA
```

## 🎯 Próximos Passos

Após confirmar que as câmeras funcionam:

1. **Configure no código principal** (`main.py`):
   ```python
   import cv2

   # Para câmera CSI
   cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

   # Para webcam USB
   cap = cv2.VideoCapture(1)
   ```

2. **Implemente processamento de visão**:
   - Detecção de QR codes
   - Reconhecimento de objetos
   - Navegação autônoma

3. **Otimize performance**:
   - Ajuste resolução e FPS
   - Use multithreading
   - Implemente buffer de frames

## 📚 Referências

- [Documentação Oficial Raspberry Pi Camera](https://www.raspberrypi.com/documentation/computers/camera_software.html)
- [OpenCV Documentation](https://docs.opencv.org/)
- [libcamera Documentation](https://libcamera.org/)