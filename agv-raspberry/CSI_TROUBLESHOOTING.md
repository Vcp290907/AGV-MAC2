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

### ❌ "detected=0"
**Causa:** Cabo flat desconectado ou câmera danificada
**Solução:**
- Verificar conexão física do cabo flat
- Certificar que conector azul da câmera está voltado para cabo USB
- Testar com outra câmera CSI

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