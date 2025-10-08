# 🧪 Teste de Câmeras - Sistema AGV

Este guia ajuda você a testar e configurar câmeras no seu Raspberry Pi 5 para o sistema AGV.

## 📋 Pré-requisitos

- Raspberry Pi 5 com Raspberry Pi OS (64-bit)
- Câmera CSI oficial ou webcam USB conectada
- Python 3.9+ instalado

## 🚀 Instalação

### 1. Instalar Dependências

Execute o script de instalação automática:

```bash
bash install_camera_deps.sh
```

Ou instale manualmente:

```bash
# Atualizar sistema
sudo apt update

# Instalar libcamera (Raspberry Pi 5)
sudo apt install -y python3-libcamera python3-kms++ libcamera-tools

# Instalar GStreamer
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libcamera

# Instalar bibliotecas Python
pip3 install opencv-python opencv-contrib-python numpy pillow
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

Este script testa:
- ✅ Câmeras USB (webcams)
- ✅ Câmera CSI (oficial)
- ✅ Câmeras IP (rede)
- ✅ Funcionalidades do OpenCV

### Teste Específico CSI

```bash
python3 test_csi_camera.py
```

Este script testa especificamente a câmera CSI com:
- ✅ libcamera (ferramentas nativas)
- ✅ OpenCV com diferentes backends
- ✅ GStreamer pipelines
- ✅ Cria script de teste contínuo

### Teste Contínuo

Após identificar uma câmera funcionando, execute:

```bash
python3 test_csi_continuous.py
```

Este script:
- 📹 Mostra preview contínuo
- 📊 Exibe FPS e estatísticas
- 💾 Salva frames periodicamente
- 🛑 Para com Ctrl+C

## 🔧 Solução de Problemas

### Câmera CSI não funciona

```bash
# Verificar se câmera está detectada
vcgencmd get_camera

# Listar dispositivos de vídeo
ls /dev/video*

# Testar libcamera diretamente
libcamera-hello -t 5000

# Verificar logs do sistema
dmesg | grep camera
```

### OpenCV não encontra câmera

```bash
# Testar índices diferentes
python3 -c "
import cv2
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Camera {i}: OK')
        cap.release()
"
```

### Erro de permissão

```bash
# Adicionar usuário ao grupo video
sudo usermod -a -G video $USER

# Reiniciar sessão
# ou reboot
sudo reboot
```

## 📊 Resultados Esperados

### Teste Básico (test_camera.py)
```
🔍 VERIFICANDO SISTEMA
📋 Sistema: Linux
🔧 Versão: 6.1.0-rpi7-rpi-v8
💻 Arquitetura: aarch64
🖥️  Modelo: Raspberry Pi 5 Model B Rev 1.0

📷 VERIFICANDO HARDWARE DE CÂMERA
🔌 Dispositivos USB conectados:
   ✅ Logitech, Inc. Webcam C270
📹 Verificando câmera CSI:
   ✅ Câmera CSI detectada

🐍 TESTANDO OPENCV
📦 OpenCV versão: 4.8.0
✅ OpenCV importado com sucesso
✅ Funcionalidades básicas do OpenCV OK

🔌 TESTANDO CÂMERAS USB
📷 Testando Câmera USB 0 (índice 0)...
   ✅ Câmera USB 0 aberta com sucesso
   📐 Resolução: 640x480
   🎬 FPS: 30.0
   📸 Testando captura de frames...
      ✅ Frame 1 capturado
      ✅ Frame 2 capturado
      ✅ Frame 3 capturado
   ✅ Câmera USB 0 funcionando corretamente!

📊 RESUMO DOS TESTES
USB Cameras: ✅ OK
CSI Camera:  ✅ OK
IP Cameras:  ❌ FALHA
```

### Teste CSI (test_csi_camera.py)
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