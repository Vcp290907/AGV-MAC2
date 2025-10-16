import cv2
import numpy as np
from picamera2 import Picamera2
import time

print('Testando câmera 0...')
try:
    picam2 = Picamera2(0)
    config = picam2.create_still_configuration(main={'format': 'RGB888', 'size': (720, 1024)})
    picam2.configure(config)
    picam2.start()

    for i in range(3):
        frame = picam2.capture_array()
        print(f'Frame {i+1}: shape={frame.shape}, média={np.mean(frame):.1f}, min/max={np.min(frame)}/{np.max(frame)}')

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        print(f'HSV médio: H={np.mean(hsv[:,:,0]):.1f}, S={np.mean(hsv[:,:,1]):.1f}, V={np.mean(hsv[:,:,2]):.1f}')

        # Testar threshold atual
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 120])
        mask = cv2.inRange(hsv, lower_black, upper_black)
        black_pixels = cv2.countNonZero(mask)
        total_pixels = mask.size
        print(f'Pixels pretos (threshold atual): {black_pixels}/{total_pixels} ({black_pixels/total_pixels:.2%})')

        time.sleep(0.5)

    picam2.stop()
    print('✅ Teste concluído')

except Exception as e:
    print(f'❌ Erro: {e}')