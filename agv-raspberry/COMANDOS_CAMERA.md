# 🚀 Guia Rápido - Teste de Câmeras no Raspberry Pi 5

## 📋 Comandos Essenciais

### 1. Verificar Sistema
```bash
# Informações do sistema
uname -a
lsb_release -a

# Verificar câmera CSI
vcgencmd get_camera

# Listar dispositivos de vídeo
ls /dev/video*
```

### 2. Instalar Dependências
```bash
# Executar script automático
bash install_camera_deps.sh

# Ou instalar manualmente
sudo apt update
sudo apt install -y python3-libcamera python3-kms++ libcamera-tools
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libcamera
pip3 install opencv-python opencv-contrib-python numpy pillow pyzbar qrcode[pil]
```

### 3. Testes Rápidos

#### Teste Básico de Todas as Câmeras
```bash
python3 test_camera.py
```

#### Teste Específico da CSI
```bash
python3 test_csi_camera.py
```

#### Teste de QR Codes
```bash
python3 test_qr_codes.py
```

#### Teste Contínuo
```bash
python3 test_csi_continuous.py
```

### 4. Testes Diretos com libcamera

#### Preview da Câmera
```bash
# Preview por 5 segundos
libcamera-hello -t 5000

# Preview em janela específica
libcamera-hello --qt-preview

# Preview com informações
libcamera-hello -v
```

#### Captura de Imagem
```bash
# Foto simples
libcamera-jpeg -o teste.jpg

# Foto com preview
libcamera-jpeg -t 2000 -o teste.jpg

# Foto em alta resolução
libcamera-jpeg --width 3280 --height 2464 -o high_res.jpg
```

#### Gravação de Vídeo
```bash
# Vídeo por 10 segundos
libcamera-vid -t 10000 -o video.h264

# Vídeo com preview
libcamera-vid --qt-preview -t 10000 -o video.h264
```

### 5. Testes com OpenCV

#### Testar Índices de Câmera
```bash
python3 -c "
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Camera {i}: OK')
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f'  Resolução: {width}x{height}, FPS: {fps}')
        cap.release()
    else:
        print(f'Camera {i}: FALHA')
"
```

#### Captura Simples com OpenCV
```bash
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    cv2.imwrite('opencv_test.jpg', frame)
    print('Imagem capturada: opencv_test.jpg')
else:
    print('Erro na captura')
cap.release()
"
```

### 6. Solução de Problemas

#### Permissões
```bash
# Adicionar usuário ao grupo video
sudo usermod -a -G video $USER

# Verificar grupos
groups

# Se não funcionar, reinicie
sudo reboot
```

#### Camera CSI não Detectada
```bash
# Verificar configuração
sudo raspi-config
# Interfacing Options -> Camera -> Enable

# Verificar detecção
vcgencmd get_camera

# Logs do sistema
dmesg | grep camera
```

#### OpenCV não Funciona
```bash
# Verificar instalação
python3 -c "import cv2; print(cv2.__version__)"

# Reinstalar se necessário
pip3 uninstall opencv-python opencv-contrib-python
pip3 install opencv-python opencv-contrib-python
```

#### GStreamer
```bash
# Testar pipeline
gst-launch-1.0 libcamerasrc ! videoconvert ! autovideosink

# Com resolução específica
gst-launch-1.0 libcamerasrc ! video/x-raw,width=640,height=480 ! videoconvert ! autovideosink
```

### 7. Performance e Otimização

#### Verificar Temperatura
```bash
# Temperatura da CPU
vcgencmd measure_temp

# Clock da CPU
vcgencmd measure_clock arm

# Voltagem
vcgencmd measure_volts
```

#### Monitor de Recursos
```bash
# CPU e memória
top

# Apenas processos Python
ps aux | grep python

# Uso de câmera
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --all
```

### 8. Integração com Sistema AGV

#### Executar Sistema Completo
```bash
# No Raspberry Pi
python3 main.py &

# Verificar se está rodando
ps aux | grep main.py

# Ver logs
tail -f /var/log/agv_system.log
```

#### Testar Comunicação com PC
```bash
# Testar API local
curl http://localhost:8080/status

# Testar comunicação WiFi
python3 test_connection.py
```

### 9. Comandos Úteis do Dia a Dia

```bash
# Listar arquivos criados pelos testes
ls -la *.jpg *.png *.h264

# Limpar arquivos de teste
rm -f teste*.jpg teste*.png video.h264

# Ver espaço em disco
df -h

# Ver processos rodando
ps aux | grep -E "(python|camera|agv)"

# Matar processos
pkill -f main.py
pkill -f test_

# Reiniciar serviços
sudo systemctl restart camera
```

### 10. Referências Rápidas

- **Documentação CSI**: https://www.raspberrypi.com/documentation/computers/camera_software.html
- **OpenCV Docs**: https://docs.opencv.org/
- **libcamera**: https://libcamera.org/
- **PyZBar**: https://pypi.org/project/pyzbar/

---

**💡 Dica**: Execute `bash run_all_camera_tests.sh` para rodar todos os testes automaticamente!