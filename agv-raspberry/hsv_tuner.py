#!/usr/bin/env python3
"""
Ferramenta interativa para calibrar HSV do marcador (azul/vermelho) com OpenCV Trackbars.
- Mostra lado a lado: imagem (BGR) e máscara.
- Permite ajustar H/S/V mínimos e máximos (duas bandas para vermelho).
- Use a CameraManager (cam 1 por padrão) para capturar frames consistentes (RGB->convertido para BGR para exibição).

Uso no Raspberry:
  python3 agv-raspberry/tools/hsv_tuner.py --color blue
  python3 agv-raspberry/tools/hsv_tuner.py --color red

Teclas:
  q  - sair
  s  - salvar snapshot do par (frame/mask)
"""
import cv2
import numpy as np
import argparse
import os
import time

try:
    from qr_reader_opencv_only import get_camera_manager
except Exception as e:
    print(f"Falha ao importar CameraManager: {e}")
    raise


def nothing(x):
    pass


def create_trackbars(color: str):
    cv2.namedWindow('mask', cv2.WINDOW_NORMAL)
    if color == 'blue':
        # H: 0-179, S/V: 0-255
        cv2.createTrackbar('H_low', 'mask', 95, 179, nothing)
        cv2.createTrackbar('H_high', 'mask', 135, 179, nothing)
        cv2.createTrackbar('S_min', 'mask', 70, 255, nothing)
        cv2.createTrackbar('V_min', 'mask', 60, 255, nothing)
    else:  # red
        cv2.createTrackbar('H1_low', 'mask', 0, 179, nothing)
        cv2.createTrackbar('H1_high', 'mask', 10, 179, nothing)
        cv2.createTrackbar('H2_low', 'mask', 170, 179, nothing)
        cv2.createTrackbar('H2_high', 'mask', 180, 179, nothing)
        cv2.createTrackbar('S_min', 'mask', 70, 255, nothing)
        cv2.createTrackbar('V_min', 'mask', 60, 255, nothing)


def get_values(color: str):
    if color == 'blue':
        h_low = cv2.getTrackbarPos('H_low', 'mask')
        h_high = cv2.getTrackbarPos('H_high', 'mask')
        s_min = cv2.getTrackbarPos('S_min', 'mask')
        v_min = cv2.getTrackbarPos('V_min', 'mask')
        return {'h_low': h_low, 'h_high': h_high, 's_min': s_min, 'v_min': v_min}
    else:
        h1_low = cv2.getTrackbarPos('H1_low', 'mask')
        h1_high = cv2.getTrackbarPos('H1_high', 'mask')
        h2_low = cv2.getTrackbarPos('H2_low', 'mask')
        h2_high = cv2.getTrackbarPos('H2_high', 'mask')
        s_min = cv2.getTrackbarPos('S_min', 'mask')
        v_min = cv2.getTrackbarPos('V_min', 'mask')
        return {'h1_low': h1_low, 'h1_high': h1_high, 'h2_low': h2_low, 'h2_high': h2_high, 's_min': s_min, 'v_min': v_min}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--color', choices=['blue', 'red'], default='blue')
    parser.add_argument('--camera', type=int, default=1)
    args = parser.parse_args()

    cm = get_camera_manager(args.camera)
    if not cm.initialize():
        print('Falha ao inicializar a câmera')
        return

    create_trackbars(args.color)
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'captures'), exist_ok=True)

    while True:
        frame_rgb = cm.capture_frame()
        if frame_rgb is None:
            continue
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

        vals = get_values(args.color)
        if args.color == 'blue':
            lower = np.array([vals['h_low'], vals['s_min'], vals['v_min']])
            upper = np.array([vals['h_high'], 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
        else:
            lower1 = np.array([vals['h1_low'], vals['s_min'], vals['v_min']])
            upper1 = np.array([vals['h1_high'], 255, 255])
            lower2 = np.array([vals['h2_low'], vals['s_min'], vals['v_min']])
            upper2 = np.array([vals['h2_high'], 255, 255])
            mask = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1), cv2.inRange(hsv, lower2, upper2))

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        vis = np.hstack((frame_bgr, mask_bgr))

        cv2.imshow('mask', vis)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('s'):
            ts = int(time.time()*1000)
            out = os.path.join(os.path.dirname(__file__), '..', 'captures', f'hsv_tuner_{args.color}_{ts}.png')
            cv2.imwrite(out, vis)
            print(f'Salvo: {out}')

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
