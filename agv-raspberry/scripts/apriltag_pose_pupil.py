#!/usr/bin/env python3
"""
AprilTag pose (tag36h11) usando pupil_apriltags, sem OpenCV (evita segfaults no OpenCV do Raspberry Pi).

Modos:
  - Imagem estática: --image caminho.jpg --calib camera_calib_charuco.json --tag-mm 30
  - (Opcional) Salvar anotado: --outimage saida.jpg

Pré-requisitos (recomendado usar venv em ~/agv_env):
  python3 -m venv ~/agv_env
  ~/agv_env/bin/pip install --upgrade pip
  ~/agv_env/bin/pip install pupil-apriltags numpy pillow
"""

import json
import argparse
import numpy as np
from PIL import Image, ImageDraw

try:
    from pupil_apriltags import Detector as PupilDetector
except Exception as e:
    PupilDetector = None


def load_calibration(path):
    with open(path, 'r') as f:
        data = json.load(f)
    K = np.array(data['camera_matrix'], dtype=np.float64)
    D = np.array(data['dist_coeffs'], dtype=np.float64)
    calib_w = int(data.get('image_width', 0) or 0)
    calib_h = int(data.get('image_height', 0) or 0)
    return K, D, (calib_w, calib_h)


def rescale_K(K, from_size, to_size):
    cw, ch = from_size
    tw, th = to_size
    if cw <= 0 or ch <= 0 or (cw == tw and ch == th):
        return K
    sx = tw / float(cw)
    sy = th / float(ch)
    K2 = K.copy()
    K2[0, 0] *= sx
    K2[1, 1] *= sy
    K2[0, 2] *= sx
    K2[1, 2] *= sy
    return K2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', type=str, required=True, help='Caminho da imagem a processar')
    ap.add_argument('--calib', type=str, required=True, help='JSON com K/D e image_width/height')
    ap.add_argument('--tag-mm', type=float, default=30.0, help='Lado do tag em mm')
    ap.add_argument('--outimage', type=str, default='', help='Se definido, salva a imagem anotada')
    args = ap.parse_args()

    if PupilDetector is None:
        print('❌ pupil_apriltags não está instalado. Use um venv e instale: pip install pupil-apriltags')
        return 2

    K, D, calib_size = load_calibration(args.calib)
    tag_size_m = args.tag_mm / 1000.0

    # Carregar imagem com PIL
    img = Image.open(args.image).convert('RGB')
    w, h = img.size
    # Converter para numpy (grayscale)
    im_np = np.asarray(img, dtype=np.uint8)
    gray = (0.299*im_np[:,:,0] + 0.587*im_np[:,:,1] + 0.114*im_np[:,:,2]).astype(np.uint8)

    # Ajustar K para o tamanho da imagem
    K_use = rescale_K(K, (calib_size[0], calib_size[1]), (w, h))

    detector = PupilDetector(families='tag36h11', nthreads=1, quad_decimate=1.0,
                             quad_sigma=0.0, refine_edges=True, decode_sharpening=0.25, debug=False)

    results = detector.detect(gray, estimate_tag_pose=True,
                              camera_params=(K_use[0,0], K_use[1,1], K_use[0,2], K_use[1,2]),
                              tag_size=tag_size_m)
    print(f'Detecções: {len(results)}')
    draw = ImageDraw.Draw(img)
    for r in results:
        pts = [(int(x), int(y)) for x, y in r.corners]
        pts_loop = pts + [pts[0]]
        for a, b in zip(pts_loop, pts_loop[1:]):
            draw.line([a, b], fill=(0,255,0), width=2)
        if getattr(r, 'pose_t', None) is not None:
            tvec = np.array(r.pose_t).reshape(-1)
            txt = f"x:{tvec[0]*100:.1f}cm y:{tvec[1]*100:.1f}cm z:{tvec[2]*100:.1f}cm"
            cx, cy = int(r.center[0]), int(r.center[1])
            draw.text((cx-60, cy-10), txt, fill=(0,255,0))

    if args.outimage:
        try:
            img.save(args.outimage)
            print(f'Salvo anotado em {args.outimage}')
        except Exception as e:
            print(f'⚠️ Falha ao salvar anotado: {e}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
