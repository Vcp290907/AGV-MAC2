from picamera2 import Picamera2
from pyzbar import pyzbar
import cv2
import os
import requests  # Para conectar à API

# Configurações da API
API_BASE_URL = "http://localhost:5000"  # Ajuste se a API estiver em outro host/porta

picam2 = Picamera2(camera_num=1)  # Usando câmera 1 como no código que funcionou melhor
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (3280, 2464)}))

picam2.start()

detected_qrs = set()  # Para evitar enviar duplicatas

while(True):
    frame = picam2.capture_array()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    decoded_objects = pyzbar.decode(enhanced)
    
    for obj in decoded_objects:
        (x, y, w, h) = obj.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        data = obj.data.decode('utf-8')
        cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Enviar para API se não foi detectado antes
        if data not in detected_qrs:
            detected_qrs.add(data)
            try:
                # Exemplo: buscar item por tag (assumindo que QR codes são tags de itens)
                response = requests.get(f"{API_BASE_URL}/itens/tag/{data}")
                if response.status_code == 200:
                    item = response.json()
                    print(f"QR detectado e item encontrado: {item['nome']} - Posição: ({item['posicao_x']}, {item['posicao_y']})")
                    # Aqui você pode adicionar lógica para navegação do AGV
                else:
                    print(f"QR detectado mas item não encontrado: {data}")
            except Exception as e:
                print(f"Erro ao conectar à API: {e}")

    cv2.imshow("Leitor de QR Code", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
