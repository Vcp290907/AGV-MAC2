# 🚨 Guia de Solução de Problemas - Câmera CSI

## Problema: Todos os testes falharam

Se você recebeu esta saída:
```
❌ libcamera preview: FALHA
❌ libcamera capture: FALHA
❌ OpenCV CSI: FALHA
❌ GStreamer: FALHA
```

## 🔍 Diagnóstico Rápido

### 1. Verificar Detecção da Câmera
```bash
vcgencmd get_camera
```
**Esperado:** `detected=1`
**Se não:** Problema de hardware/conexão

### 2. Verificar libcamera
```bash
libcamera-hello --version
```
**Se erro:** libcamera não instalado

### 3. Verificar Permissões
```bash
groups $USER
```
**Deve conter:** `video`

## 🛠️ Soluções Passo a Passo

### PASSO 1: Diagnóstico Completo
```bash
bash diagnose_csi_camera.sh
```

### PASSO 2: Correção Automática
```bash
bash fix_csi_camera.sh
```

### PASSO 3: Habilitar Câmera Manualmente
```bash
sudo raspi-config
```
- Interfacing Options
- Camera
- Enable
- Finish
- Reboot

### PASSO 4: Reiniciar Sistema
```bash
sudo reboot
```

### PASSO 5: Testar Novamente
```bash
python3 test_csi_camera.py
```

## 🔧 Correções Manuais (se automático falhar)

### Instalar libcamera
```bash
sudo apt update
sudo apt install -y python3-libcamera python3-kms++ libcamera-tools
```

### Configurar /boot/firmware/config.txt
```bash
sudo nano /boot/firmware/config.txt
```
Adicionar no final:
```
camera_auto_detect=1
```

### Corrigir Permissões
```bash
sudo usermod -a -G video $USER
# Logout e login novamente
```

### Instalar OpenCV
```bash
pip3 install opencv-python opencv-contrib-python
```

## 🐛 Problemas Comuns e Soluções

### ❌ "detected=0" (Câmera Oficial)
**Causa:** Cabo flat desconectado ou câmera danificada
**Solução:**
- Verificar conexão física do cabo flat
- Certificar que conector azul da câmera está voltado para cabo USB
- Testar com outra câmera CSI

### ❌ "detected=0" (Câmera Chinesa) - NORMAL!
**IMPORTANTE:** Para câmeras chinesas CSI, `vcgencmd get_camera` **SEMPRE** mostra `detected=0`
**Isso é normal!** Câmeras chinesas não são detectadas pelo firmware da Raspberry Pi.

**Verificação correta para câmeras chinesas:**
```bash
# Verificar dispositivos V4L2
v4l2-ctl --list-devices

# Deve mostrar algo como:
/dev/video0
/dev/video1
```

**Teste correto:**
```bash
python3 test_chinese_csi_camera.py
```

### ❌ "libcamera não encontrado"
**Causa:** Pacotes não instalados
**Solução:**
```bash
sudo apt install -y python3-libcamera libcamera-tools
```

### ❌ "Permissões insuficientes"
**Causa:** Usuário não no grupo video
**Solução:**
```bash
sudo usermod -a -G video $USER
sudo reboot
```

### ❌ OpenCV não funciona
**Causa:** Biblioteca não instalada ou câmera não acessível
**Solução:**
```bash
pip3 install opencv-python
# Verificar se câmera está habilitada
```

## 🇨🇳 CÂMERAS CSI CHINESAS - GUIA ESPECÍFICO

### Detecção Normal: "detected=0"
**IMPORTANTE:** Câmeras chinesas CSI **sempre** mostram `detected=0` no `vcgencmd get_camera`. Isso é **normal**!

### Verificação Correta
```bash
# Verificar dispositivos V4L2
v4l2-ctl --list-devices

# Deve mostrar:
/dev/video0
/dev/video1
```

### Teste Específico
```bash
python3 test_chinese_csi_camera.py
```

### Problemas Específicos de Câmeras Chinesas

#### ❌ Câmera Não Aparece em /dev/video*
**Causa:** Falta de alimentação ou drivers
**Solução:**
```bash
# Verificar alimentação (muitas câmeras chinesas precisam de 5V separado)
# Instalar drivers V4L2
sudo apt install v4l-utils

# Verificar módulos
lsmod | grep v4l
```

#### ❌ Câmera Detectada mas Sem Imagem
**Causa:** Formato incorreto ou timing
**Solução:**
```bash
# Verificar formatos suportados
v4l2-ctl --list-formats-ext -d /dev/video0

# Configurar formato
v4l2-ctl --device=/dev/video0 --set-fmt-video=width=640,height=480,pixelformat=YUYV
```

#### ❌ OpenCV Não Funciona
**Solução:**
```python
import cv2
import time

# Tentar diferentes índices
for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
    if cap.isOpened():
        time.sleep(2)  # Aguardar inicialização
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        ret, frame = cap.read()
        if ret:
            print(f"Câmera funcionando no índice {i}")
        cap.release()
        break
```

## 🧪 Testes Individuais

### Teste libcamera Básico
```bash
libcamera-hello -t 5000
```

### Teste OpenCV Básico
```bash
python3 -c "
import cv2
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
print('Aberto:', cap.isOpened())
ret, frame = cap.read()
print('Frame capturado:', ret)
cap.release()
"
```

### Teste GStreamer
```bash
gst-launch-1.0 libcamerasrc ! videoconvert ! autovideosink
```

## 📞 Quando Pedir Ajuda

Se nada funcionar, forneça estas informações:

1. **Modelo do Raspberry Pi:** `cat /proc/device-tree/model`
2. **Versão do OS:** `lsb_release -a`
3. **Saída de diagnóstico:** `bash diagnose_csi_camera.sh`
4. **Logs do sistema:** `dmesg | grep -i camera`
5. **Conexão física:** Descreva como a câmera está conectada

## 🔗 Links Úteis

- [Documentação Oficial CSI](https://www.raspberrypi.com/documentation/computers/camera_software.html)
- [Troubleshooting Camera](https://www.raspberrypi.com/documentation/computers/camera_software.html#troubleshooting)
- [Raspberry Pi Camera Module](https://www.raspberrypi.com/products/camera-module-3/)