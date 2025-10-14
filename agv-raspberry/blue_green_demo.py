#!/usr/bin/env python3
import time
from line_following_navigation import LineFollowingNavigation

def main():
    nav = LineFollowingNavigation(visual_feedback=False)
    if not nav.initialize():
        print("Falha na inicialização")
        return

    ok = nav.go_until_blue_then_turn_right_until_green(
        drive_speed=22,
        turn_speed_fast=35,
        turn_speed_slow=14,
        timeout_drive=25.0,
        timeout_turn=15.0,
        min_turn_time_s=1.2,           # garante girar pelo menos 1.2s antes de aceitar verde
        green_persist_frames=3,         # requer 3 frames seguidos de verde na ROI inferior
        green_min_area=1800,            # área mínima do quadrado verde
        turn_direction='direita',       # direção desejada ("direita" ou "esquerda"),
        scan_shelf_qr_after_turn=True,
        shelf_cam_index=0,           # usar câmera 0 para a estante
        shelf_scan_time_s=3.0,
        shelf_scan_debug=True,       # exporta imagem e txt
        shelf_debug_dir=None,        # default: 'captures' ao lado do script
        shelf_debug_prefix='shelf_qr_debug',
    )
    print(f"Resultado da rotina azul->verde: {ok}")
    time.sleep(1)
    nav.basic_nav.parar()

if __name__ == "__main__":
    main()
