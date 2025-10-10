from picamera2 import Picamera2
from pyzbar import pyzbar
import cv2
import os

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
picam2.start()

# Initialize OpenCV QR Code Detector
qr_detector = cv2.QRCodeDetector()

while(True):
    frame = picam2.capture_array()

    # Convert to grayscale for better detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect and decode QR codes using OpenCV
    retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
    
    if retval:
        for i, data in enumerate(decoded_info):
            if data:  # Only if data is not empty
                # Get the points for the QR code
                pts = points[i].astype(int)
                
                # Draw the polygon around the QR code
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                
                # Put the decoded text
                cv2.putText(frame, data, (pts[0][0], pts[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Mostra o frame com os QR codes detectados
    cv2.imshow("Leitor de QR Code", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
