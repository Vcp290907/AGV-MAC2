#!/usr/bin/env python3
"""
Validador simples da câmera com Picamera2.

- Abre preview em 640x480 com formato XRGB8888 (config mais estável no Pi 5)
- Clique com o mouse salva uma imagem em ./validacao/
- Tecla 'q' fecha

Uso:
  python3 picam_validate.py --camera-index 0 --width 640 --height 480 --pixfmt XRGB8888
"""

import os
import argparse
import datetime as dt
import numpy as np
import cv2

try:
    from picamera2 import Picamera2
except Exception as e:
    print(f"❌ Picamera2 não disponível: {e}")
    raise SystemExit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--camera-index', type=int, default=0)
    ap.add_argument('--width', type=int, default=640)
    ap.add_argument('--height', type=int, default=480)
    ap.add_argument('--pixfmt', type=str, default='XRGB8888', choices=['XRGB8888', 'RGB888'])
    ap.add_argument('--outdir', type=str, default='validacao')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Abrir câmera
    picam2 = Picamera2(int(args.camera_index))
    cfg = picam2.create_preview_configuration(main={"format": args.pixfmt, "size": (int(args.width), int(args.height))})
    picam2.configure(cfg)
    picam2.start()

    win = "Camera"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)

    saved = 0
    ctx = {"frame": None}

    def on_mouse(event, x, y, flags, param):
        nonlocal saved
        if event == cv2.EVENT_LBUTTONDOWN:
            frm = param.get("frame")
            if frm is None:
                return
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(args.outdir, f"imagemValidacao_{ts}.jpg")
            try:
                cv2.imwrite(path, frm)
                saved += 1
                print(f"💾 Salvo: {path}")
            except Exception as e:
                print(f"❌ Falha ao salvar: {e}")

    cv2.setMouseCallback(win, on_mouse, ctx)

    try:
        while True:
            frm = picam2.capture_array()
            if frm is None:
                continue
            frm = np.ascontiguousarray(frm, dtype=np.uint8)
            # Converter para BGR conforme formato
            if args.pixfmt == 'RGB888':
                bgr = cv2.cvtColor(frm, cv2.COLOR_RGB2BGR)
            else:
                # XRGB8888: [X, R, G, B] -> [R, G, B] -> BGR
                if frm.ndim == 3 and frm.shape[2] == 4:
                    rgb = frm[:, :, 1:4]
                    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                else:
                    bgr = frm.copy()

            ctx["frame"] = bgr
            vis = bgr.copy()
            cv2.putText(vis, f"Clique = salvar | q = sair | salvos: {saved}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.imshow(win, vis)
            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                break
    finally:
        picam2.stop()
        cv2.destroyAllWindows()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
