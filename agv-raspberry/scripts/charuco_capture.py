#!/usr/bin/env python3
"""
Captura simples para ChArUco: apenas visualizar e salvar fotos.

- Mostra a câmera em tempo real (Picamera2 ou OpenCV)
- Clique do mouse ou tecla 's' / ESPAÇO salva uma imagem
- 'q' ou ESC sai

Use para coletar ~20-30 fotos em ângulos/posições diferentes da folha ChArUco.
Depois rode o calibrador.
"""

import os
import time
import argparse
import datetime
import numpy as np
import cv2

# Suporte opcional a Picamera2
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False


def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Preview e captura simples para ChArUco")
    parser.add_argument("--backend", choices=["auto", "picam", "opencv"], default="auto", help="Backend de captura")
    parser.add_argument("--cam", type=int, default=0, help="Índice da câmera (0/1)")
    parser.add_argument("--width", type=int, default=3280)
    parser.add_argument("--height", type=int, default=2464)
    parser.add_argument("--outdir", type=str, default="./charuco_capturas")
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270], help="Rotacionar imagem (graus)")
    args = parser.parse_args()

    try:
        cv2.setNumThreads(1)
    except Exception:
        pass

    ensure_dir(args.outdir)
    window = "ChArUco - Preview e Captura"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    picam2 = None
    cap = None
    use_picam = (args.backend == "picam") or (args.backend == "auto" and PICAMERA2_AVAILABLE)

    if use_picam and PICAMERA2_AVAILABLE:
        try:
            picam2 = Picamera2(args.cam)
            cfg = picam2.create_preview_configuration(main={"format": 'RGB888', "size": (int(args.width), int(args.height))})
            picam2.configure(cfg)
            picam2.start()
        except Exception as e:
            print(f"⚠️ Falha Picamera2: {e}. Tentar OpenCV...")
            picam2 = None

    if picam2 is None:
        cap = cv2.VideoCapture(args.cam)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(args.width))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(args.height))
        if not cap.isOpened():
            print("❌ Não foi possível abrir a câmera")
            return 1

    saved_count = 0
    last_click = [0, 0]

    def on_mouse(event, x, y, flags, param):
        nonlocal saved_count, last_click
        if event == cv2.EVENT_LBUTTONDOWN:
            frame = param.get("frame")
            if frame is None:
                return
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(args.outdir, f"charuco_{ts}.jpg")
            try:
                cv2.imwrite(path, frame)
                saved_count += 1
                last_click = [x, y]
                print(f"💾 Salvo: {path}")
            except Exception as e:
                print(f"❌ Erro ao salvar: {e}")

    ctx = {"frame": None}
    cv2.setMouseCallback(window, on_mouse, ctx)

    try:
        while True:
            if picam2 is not None:
                frm = picam2.capture_array()
                if frm is None:
                    time.sleep(0.01)
                    continue
                # Picamera2 retorna RGB -> converter para BGR para exibição/salvar
                frm = np.ascontiguousarray(frm, dtype=np.uint8)
                frame_bgr = cv2.cvtColor(frm, cv2.COLOR_RGB2BGR)
            else:
                ok, frm = cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue
                frame_bgr = np.ascontiguousarray(frm, dtype=np.uint8)

            # Rotação se necessário
            if args.rotate == 90:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
            elif args.rotate == 180:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_180)
            elif args.rotate == 270:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

            h, w = frame_bgr.shape[:2]
            vis = frame_bgr.copy()

            # Guias simples: mira central e texto de instruções
            cx, cy = w // 2, h // 2
            cv2.drawMarker(vis, (cx, cy), (0, 255, 255), markerType=cv2.MARKER_CROSS, markerSize=24, thickness=2)
            cv2.putText(vis, "Clique ou [S]/[ESPACO] = salvar | [Q] = sair", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(vis, f"Capturas: {saved_count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

            # Marcar último clique (feedback)
            if last_click != [0, 0]:
                cv2.circle(vis, tuple(last_click), 10, (0, 255, 0), 2)

            ctx["frame"] = frame_bgr
            cv2.imshow(window, vis)
            k = cv2.waitKey(1) & 0xFF
            if k in (ord('q'), 27):
                break
            if k in (ord('s'), ord('S'), 32):  # 's' ou SPACE
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = os.path.join(args.outdir, f"charuco_{ts}.jpg")
                try:
                    cv2.imwrite(path, frame_bgr)
                    saved_count += 1
                    print(f"💾 Salvo: {path}")
                except Exception as e:
                    print(f"❌ Erro ao salvar: {e}")

    finally:
        if cap is not None:
            cap.release()
        if picam2 is not None:
            try:
                picam2.stop()
                picam2.close()
            except Exception:
                pass
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
