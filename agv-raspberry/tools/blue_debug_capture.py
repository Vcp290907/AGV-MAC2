#!/usr/bin/env python3
"""
Captura um frame da câmera principal (cam 1) e salva visuais de debug da detecção do azul
para validar rapidamente thresholds, ROI e diretório de saída.

Uso (no Raspberry):
  python3 agv-raspberry/tools/blue_debug_capture.py
Sai:
  agv-raspberry/captures/blue_debug_*.png
  agv-raspberry/captures/blue_frame_*.png
"""
import os
import time
import cv2
import numpy as np

try:
    from config import NAVIGATION_CONFIG
except Exception as e:
    print(f"Falha ao importar config: {e}")
    NAVIGATION_CONFIG = {}

try:
    from qr_reader_opencv_only import get_camera_manager
except Exception as e:
    print(f"Falha ao importar CameraManager: {e}")
    raise

SNAP_DIR = os.path.join(os.path.dirname(__file__), '..', 'captures')
SNAP_DIR = os.path.abspath(SNAP_DIR)
os.makedirs(SNAP_DIR, exist_ok=True)


def save_debug_images(frame_rgb):
    cfg = NAVIGATION_CONFIG.get('markers', {}).get('blue', {})
    h_low = int(cfg.get('h_low', 95))
    h_high = int(cfg.get('h_high', 135))
    s_min = int(cfg.get('s_min', 70))
    v_min = int(cfg.get('v_min', 60))
    roi_y_start_frac = float(cfg.get('roi_y_start_frac', 0.45))

    H, W = frame_rgb.shape[:2]
    y1 = int(max(0, min(H - 1, H * roi_y_start_frac)))
    roi = frame_rgb[y1:H, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    lower_blue = np.array([h_low, s_min, v_min])
    upper_blue = np.array([h_high, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    vis_dbg = np.hstack((roi_bgr, mask_bgr))
    for c in contours[:3]:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(vis_dbg, (x, y), (x + w, y + h), (255, 0, 0), 2)
    cv2.putText(vis_dbg, f"HSV H:[{h_low},{h_high}] S>={s_min} V>={v_min}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    ts = int(time.time() * 1000)
    out_dbg = os.path.join(SNAP_DIR, f"blue_debug_{ts}.png")
    out_full = os.path.join(SNAP_DIR, f"blue_frame_{ts}.png")
    cv2.imwrite(out_dbg, vis_dbg)
    cv2.imwrite(out_full, cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))
    print(f"Salvo: {out_dbg}\nSalvo: {out_full}")


def main():
    cam_id = 1  # câmera de linha/azul
    cm = get_camera_manager(cam_id)
    if not cm.initialize():
        print("Falha ao inicializar câmera")
        return
    frame = cm.capture_frame()
    if frame is None:
        print("Falha ao capturar frame")
        return
    # frame vem em RGB da Picamera2
    save_debug_images(frame)


if __name__ == "__main__":
    main()
