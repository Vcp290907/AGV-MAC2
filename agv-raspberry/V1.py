from picamera2 import Picamera2
from pyzbar import pyzbar
import cv2
import os

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1640, 1232)}))
picam2.start()

cv2.namedWindow("Camera")

while(True):
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    decoded_objects = pyzbar.decode(frame)
    
    # Desenha um retângulo e exibe o texto do QR code
    for obj in decoded_objects:
        # Desenha o retângulo
        (x, y, w, h) = obj.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Decodifica o dado e o exibe na tela
        data = obj.data.decode('utf-8')
        cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Mostra o frame com os QR codes detectados
    cv2.imshow("Leitor de QR Code", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
