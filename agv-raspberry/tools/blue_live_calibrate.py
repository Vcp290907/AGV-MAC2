#!/usr/bin/env python3
"""
Calibrador ao vivo para detecção do marcador azul (HSV + ROI + gates).

Use isto no Raspberry para ajustar rapidamente H/S/V e filtros geométricos, 
vendo a detecção em tempo real. Não altera o seu código principal.

Como usar:
  python3 agv-raspberry/tools/blue_live_calibrate.py

Teclas:
  q  -> sair
  s  -> salvar snapshot em agv-raspberry/captures
"""
import os
import time
import cv2
import numpy as np

try:
    from config import NAVIGATION_CONFIG
except Exception as e:
    print(f"Falha ao importar NAVIGATION_CONFIG: {e}")
    NAVIGATION_CONFIG = {}

try:
    # Usa o mesmo CameraManager do projeto para evitar conflitos
    from qr_reader_opencv_only import get_camera_manager
except Exception as e:
    print(f"Falha ao importar CameraManager: {e}")
    raise


SNAP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'captures'))
os.makedirs(SNAP_DIR, exist_ok=True)


def nothing(_):
    pass


def create_trackbars(win: str, cfg: dict):
    cv2.createTrackbar('H_low', win, int(cfg.get('h_low', 95)), 179, nothing)
    cv2.createTrackbar('H_high', win, int(cfg.get('h_high', 135)), 179, nothing)
    cv2.createTrackbar('S_min', win, int(cfg.get('s_min', 60)), 255, nothing)
    cv2.createTrackbar('V_min', win, int(cfg.get('v_min', 50)), 255, nothing)
    cv2.createTrackbar('ROI_y% (base)', win, int(float(cfg.get('roi_y_start_frac', 0.45)) * 100), 90, nothing)

    # Gates geométricos principais
    cv2.createTrackbar('min_area', win, int(cfg.get('min_area', 250)), 5000, nothing)
    cv2.createTrackbar('min_size', win, int(cfg.get('min_size_px', 30)), 300, nothing)
    cv2.createTrackbar('aspect_min x100', win, int(float(cfg.get('aspect_min', 0.7)) * 100), 300, nothing)
    cv2.createTrackbar('aspect_max x100', win, int(float(cfg.get('aspect_max', 1.4)) * 100), 300, nothing)
    cv2.createTrackbar('extent_min x100', win, int(float(cfg.get('extent_min', 0.50)) * 100), 100, nothing)
    cv2.createTrackbar('bbox_bottom_min%H', win, int(float(cfg.get('bbox_bottom_min_frac', 0.55)) * 100), 100, nothing)
    cv2.createTrackbar('min_y%H', win, int(float(cfg.get('min_y_frac', 0.40)) * 100), 100, nothing)
    cv2.createTrackbar('edge_margin_px', win, int(cfg.get('edge_margin_px', 10)), 200, nothing)
    cv2.createTrackbar('cx_min%W', win, int(float(cfg.get('center_x_min_frac', 0.20)) * 100), 100, nothing)
    cv2.createTrackbar('cx_max%W', win, int(float(cfg.get('center_x_max_frac', 0.80)) * 100), 100, nothing)

    # Gate da linha preta logo abaixo do azul
    cv2.createTrackbar('line_gate_black% x100', win, int(float(cfg.get('line_gate_min_black_frac', 0.12)) * 100), 100, nothing)
    cv2.createTrackbar('line_gate_h%bbox', win, int(float(cfg.get('line_gate_strip_h_frac', 0.18)) * 100), 100, nothing)


def read_trackbars(win: str):
    # HSV
    h_low = cv2.getTrackbarPos('H_low', win)
    h_high = cv2.getTrackbarPos('H_high', win)
    s_min = cv2.getTrackbarPos('S_min', win)
    v_min = cv2.getTrackbarPos('V_min', win)
    roi_y_frac = cv2.getTrackbarPos('ROI_y% (base)', win) / 100.0

    # Gates
    min_area = cv2.getTrackbarPos('min_area', win)
    min_size = cv2.getTrackbarPos('min_size', win)
    aspect_min = cv2.getTrackbarPos('aspect_min x100', win) / 100.0
    aspect_max = cv2.getTrackbarPos('aspect_max x100', win) / 100.0
    extent_min = cv2.getTrackbarPos('extent_min x100', win) / 100.0
    bbox_bottom_min_frac = cv2.getTrackbarPos('bbox_bottom_min%H', win) / 100.0
    min_y_frac = cv2.getTrackbarPos('min_y%H', win) / 100.0
    edge_margin_px = cv2.getTrackbarPos('edge_margin_px', win)
    cx_min_frac = cv2.getTrackbarPos('cx_min%W', win) / 100.0
    cx_max_frac = cv2.getTrackbarPos('cx_max%W', win) / 100.0
    line_gate_black = cv2.getTrackbarPos('line_gate_black% x100', win) / 100.0
    line_gate_h_frac = cv2.getTrackbarPos('line_gate_h%bbox', win) / 100.0

    return {
        'h_low': h_low, 'h_high': h_high, 's_min': s_min, 'v_min': v_min,
        'roi_y_start_frac': roi_y_frac,
        'min_area': min_area, 'min_size_px': min_size,
        'aspect_min': aspect_min, 'aspect_max': aspect_max, 'extent_min': extent_min,
        'bbox_bottom_min_frac': bbox_bottom_min_frac,
        'min_y_frac': min_y_frac, 'edge_margin_px': edge_margin_px,
        'center_x_min_frac': cx_min_frac, 'center_x_max_frac': cx_max_frac,
        'line_gate_min_black_frac': line_gate_black, 'line_gate_strip_h_frac': line_gate_h_frac,
    }


def apply_detection(frame_rgb, params):
    H, W = frame_rgb.shape[:2]
    y1 = int(max(0, min(H - 1, H * float(params['roi_y_start_frac']))))
    roi = frame_rgb[y1:H, :]

    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    lower_blue = np.array([int(params['h_low']), int(params['s_min']), int(params['v_min'])])
    upper_blue = np.array([int(params['h_high']), 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Visualizações
    roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
    vis = roi_bgr.copy()

    chosen = None
    for c in contours:
        area = cv2.contourArea(c)
        if area < params['min_area']:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if w < params['min_size_px'] or h < params['min_size_px']:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        vertices = len(approx)
        aspect_ratio = float(w) / h if h > 0 else 999
        extent = area / float(w * h) if (w * h) > 0 else 0.0

        x0, y0 = x, y + y1
        bbox_bottom = y0 + h
        cx = x0 + w // 2

        # Desenho do bbox e textos de debug
        cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(vis, f"A:{int(area)} asp:{aspect_ratio:.2f} ext:{extent:.2f} v:{vertices}", (x, max(10, y - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

        # Aplicar gates (mesma lógica do código principal)
        if not (4 <= vertices <= 8 and params['aspect_min'] <= aspect_ratio <= params['aspect_max'] and extent >= params['extent_min']):
            continue
        if bbox_bottom < int(H * params['bbox_bottom_min_frac']):
            continue
        if y0 < int(H * params['min_y_frac']):
            continue
        if x0 < int(params['edge_margin_px']) or (x0 + w) > (W - int(params['edge_margin_px'])):
            continue
        if not (int(W * params['center_x_min_frac']) <= cx <= int(W * params['center_x_max_frac'])):
            continue

        # Gate da linha preta logo abaixo do bbox (usando HSV em BGR do frame completo)
        ok_line = True
        req_black_frac = float(params['line_gate_min_black_frac'])
        if req_black_frac > 0.0:
            strip_y1 = min(H - 1, y0 + h)
            strip_y2 = min(H, strip_y1 + max(2, int(h * float(params['line_gate_strip_h_frac']))))
            if strip_y2 > strip_y1:
                # strip no frame original (RGB -> BGR -> HSV)
                strip = frame_rgb[strip_y1:strip_y2, max(0, x0):min(W, x0 + w)]
                strip_bgr = cv2.cvtColor(strip, cv2.COLOR_RGB2BGR)
                strip_hsv = cv2.cvtColor(strip_bgr, cv2.COLOR_BGR2HSV)
                lower_black = np.array([0, 0, 0])
                upper_black = np.array([180, 255, 200])
                m_black = cv2.inRange(strip_hsv, lower_black, upper_black)
                black_frac = float(np.count_nonzero(m_black)) / float(m_black.size if m_black.size > 0 else 1)
                ok_line = black_frac >= req_black_frac
                # desenhar faixa
                cv2.rectangle(vis, (x, strip_y1 - y1), (x + w, strip_y2 - y1), (0, 255 if ok_line else 0, 0 if ok_line else 255), 2)
                cv2.putText(vis, f"black={black_frac:.2f}", (x, min(H - y1 - 5, strip_y2 - y1 + 14)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255 if ok_line else 0, 0 if ok_line else 255), 1)

        if ok_line:
            chosen = {'bbox': (x0, y0, w, h), 'area': area, 'center': (x0 + w//2, y0 + h//2)}
            # desenhar centro
            cv2.circle(vis, (x, y), 3, (0, 255, 255), -1)
            break

    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    out = np.hstack((vis, mask_bgr))
    return out, chosen


def main():
    blue_cfg = (NAVIGATION_CONFIG.get('markers', {}).get('blue', {}) if isinstance(NAVIGATION_CONFIG, dict) else {})
    win = 'Blue Calibrator (HSV)'
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 1280, 720)
    create_trackbars(win, blue_cfg)

    cam_id = 1  # câmera de linha/azul
    cm = get_camera_manager(cam_id)
    if not cm.initialize():
        print('Falha ao inicializar câmera')
        return

    print('Pressione q para sair, s para salvar snapshot')

    last_save = 0
    while True:
        frame_rgb = cm.capture_frame()
        if frame_rgb is None:
            print('Falha ao capturar frame')
            break

        params = read_trackbars(win)
        vis, det = apply_detection(frame_rgb, params)

        # Texto com HSV atual
        txt = f"H:[{params['h_low']},{params['h_high']}] S>={params['s_min']} V>={params['v_min']}"
        cv2.putText(vis, txt, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        if det:
            x, y, w, h = det['bbox']
            cv2.putText(vis, f"DETECTADO area:{int(det['area'])}", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
        else:
            cv2.putText(vis, "nao detectado", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow(win, vis)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('s'):
            # salvar imagem + params
            now = time.time()
            if now - last_save > 0.3:
                last_save = now
                ts = int(now * 1000)
                out_img = os.path.join(SNAP_DIR, f'blue_live_{ts}.png')
                cv2.imwrite(out_img, vis)
                print(f'Salvo: {out_img}')

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
