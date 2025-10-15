#!/usr/bin/env python3
"""
Preview local da câmera do AGV (sem mover motores)
Mostra linha, quadrado verde e QR em uma janela OpenCV.

Use este script diretamente no Raspberry (ex.: via VNC) para checar enquadramento.

Controles:
- q / ESC: sair
"""

import os
import argparse
from line_following_navigation import LineFollowingNavigation


def main():
    parser = argparse.ArgumentParser(description="Preview local da câmera do AGV")
    parser.add_argument("--cam", type=int, default=None, help="Índice da câmera (0 ou 1)")
    args = parser.parse_args()

    # Permitir seleção de câmera via argumento
    if args.cam is not None:
        os.environ["CAMERA_INDEX"] = str(args.cam)

    nav = LineFollowingNavigation(visual_feedback=True)

    # Ajustar também direto no detector, se passado
    if args.cam is not None:
        try:
            nav.line_detector.camera_index = int(args.cam)
        except Exception:
            pass

    # Apenas roda o preview (loop interno até 'q' ou ESC)
    try:
        nav.start_visual_preview()
    finally:
        nav.disable_visual_feedback()
        nav.cleanup()


if __name__ == "__main__":
    main()
