#!/usr/bin/env python3
"""
Demo de detecção e pose de AprilTags (36h11) usando calibração da câmera.

Pré-requisitos:
 1) Calibre a câmera com scripts/calibrate_charuco.py ou calibrate_charuco_from_images.py (gera camera_calib_charuco.json).
 2) Imprima a folha de AprilTags (30mm cada) em 100%.

Uso:
  - Rode este script. Ele detecta AprilTags, desenha e estima pose 3D.
  - Pressione 'q' para sair.

Agora com suporte a Picamera2 para Raspberry Pi (--backend picam ou auto se disponível).
"""

import json
import time
import argparse
import numpy as np
import cv2

# Suporte opcional a Picamera2 (Raspberry Pi)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False


def load_calibration(path):
    with open(path, 'r') as f:
        data = json.load(f)
    K = np.array(data['camera_matrix'], dtype=np.float64)
    D = np.array(data['dist_coeffs'], dtype=np.float64)
    calib_w = int(data.get('image_width', 0) or 0)
    calib_h = int(data.get('image_height', 0) or 0)
    return K, D, (calib_w, calib_h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--camera-index', type=int, default=0, help='Índice da câmera (tanto para OpenCV quanto Picamera2)')
    ap.add_argument('--backend', type=str, default='auto', choices=['auto', 'picam', 'opencv'], help='Backend de captura')
    ap.add_argument('--width', type=int, default=2560, help='Largura de captura/preview')
    ap.add_argument('--height', type=int, default=1920, help='Altura de captura/preview')
    ap.add_argument('--pixfmt', type=str, default='XRGB8888', choices=['RGB888', 'XRGB8888'], help='Formato de pixel Picamera2')
    ap.add_argument('--calib', type=str, default='camera_calib_charuco.json')
    ap.add_argument('--tag-mm', type=float, default=30.0, help='Lado do tag em mm (ex.: 30.0)')
    ap.add_argument('--force-legacy', action='store_true', help='Força usar aruco.detectMarkers (evita ArucoDetector)')
    ap.add_argument('--no-axes', action='store_true', help='Não desenha eixos 3D (evita possíveis crashes em drawFrameAxes)')
    ap.add_argument('--detector', type=str, default='opencv', choices=['opencv', 'pupil'], help='Detector de AprilTag: OpenCV ArUco ou pupil_apriltags')
    ap.add_argument('--no-window', action='store_true', help='Não abre janela (headless); imprime resumo no console')
    ap.add_argument('--frames', type=int, default=0, help='Número máximo de frames para processar (0 = infinito)')
    ap.add_argument('--image', type=str, default='', help='Processa uma imagem estática (pula captura da câmera)')
    ap.add_argument('--outimage', type=str, default='', help='Se definido, salva a imagem anotada neste caminho')
    ap.add_argument('--save-out', type=str, default='', help='(Live) Salva o último frame anotado neste caminho ao finalizar')
    args = ap.parse_args()

    # Tentar reduzir threads do OpenCV (estabilidade em ARM)
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass
    try:
        cv2.setUseOptimized(False)
    except Exception:
        pass

    K, D, calib_size = load_calibration(args.calib)
    tag_size_m = args.tag_mm / 1000.0

    aruco = cv2.aruco
    DICT = getattr(aruco, 'DICT_APRILTAG_36h11')
    dictionary = aruco.getPredefinedDictionary(DICT)

    try:
        det_params = aruco.DetectorParameters()
    except AttributeError:
        det_params = aruco.DetectorParameters_create()

    # Detector via OpenCV (padrão) ou via pupil_apriltags
    detector = None
    pupil_detector = None
    if args.detector == 'opencv':
        if not args.force_legacy:
            try:
                detector = aruco.ArucoDetector(dictionary, det_params)
            except Exception:
                detector = None
    else:
        try:
            from pupil_apriltags import Detector as PupilDetector
            pupil_detector = PupilDetector(families='tag36h11', nthreads=1, quad_decimate=1.0, quad_sigma=0.0,
                                           refine_edges=True, decode_sharpening=0.25, debug=False)
        except Exception as e:
            print(f"⚠️ pupil_apriltags não disponível ({e}). Voltando para OpenCV.")
            args.detector = 'opencv'
            if not args.force_legacy:
                try:
                    detector = aruco.ArucoDetector(dictionary, det_params)
                except Exception:
                    detector = None

    # Se for imagem estática, processa e sai
    if args.image:
        img = cv2.imread(args.image)
        if img is None:
            print(f"❌ Não foi possível ler a imagem: {args.image}")
            return 2
        frame = np.ascontiguousarray(img, dtype=np.uint8)
        h, w = frame.shape[:2]
        cw, ch = calib_size
        K_use = K.copy()
        if cw > 0 and ch > 0 and (w != cw or h != ch):
            sx = w / float(cw)
            sy = h / float(ch)
            K_use[0,0] *= sx; K_use[1,1] *= sy; K_use[0,2] *= sx; K_use[1,2] *= sy
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        vis = frame.copy()
        det_count = 0
        if args.detector == 'opencv':
            if detector is not None:
                corners, ids, _ = detector.detectMarkers(gray)
            else:
                corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=det_params)
            if ids is not None and len(ids) > 0:
                det_count = len(ids)
                aruco.drawDetectedMarkers(vis, corners, ids)
                for c in corners:
                    rvec, tvec, _ = aruco.estimatePoseSingleMarkers(c, tag_size_m, K_use, D)
                    if rvec is not None and tvec is not None and not args.no_axes:
                        try:
                            cv2.drawFrameAxes(vis, K_use, D, rvec.reshape(-1,3)[0], tvec.reshape(-1,3)[0], tag_size_m*0.5)
                        except Exception:
                            pass
        else:
            try:
                from pupil_apriltags import Detector as PupilDetector
                pupil_detector = PupilDetector(families='tag36h11')
                results = pupil_detector.detect(gray, estimate_tag_pose=True,
                                                camera_params=(K_use[0,0], K_use[1,1], K_use[0,2], K_use[1,2]),
                                                tag_size=tag_size_m)
            except Exception:
                results = []
            det_count = len(results)
            for r in results:
                pts = r.corners.astype(int)
                for j in range(4):
                    cv2.line(vis, tuple(pts[j]), tuple(pts[(j+1)%4]), (0,255,0), 2)

        print(f"Detecções: {det_count}")
        if args.outimage:
            try:
                cv2.imwrite(args.outimage, vis)
            except Exception:
                pass
        if not args.no_window:
            cv2.imshow('AprilTag Pose - Image', vis)
            cv2.waitKey(0)
        return 0

    # Inicializa captura
    picam2 = None
    cap = None
    use_picam = (args.backend == 'picam') or (args.backend == 'auto' and PICAMERA2_AVAILABLE)

    if use_picam and PICAMERA2_AVAILABLE:
        try:
            picam2 = Picamera2(int(args.camera_index))
            # Usar configuração de preview como no exemplo fornecido
            cfg = picam2.create_preview_configuration(main={"format": args.pixfmt, "size": (int(args.width), int(args.height))})
            picam2.configure(cfg)
            picam2.start()
        except Exception as e:
            print(f"⚠️ Falha ao iniciar Picamera2 ({e}). Usando OpenCV...")
            picam2 = None

    if picam2 is None:
        cap = cv2.VideoCapture(args.camera_index)
        if args.width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(args.width))
        if args.height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(args.height))
        if not cap.isOpened():
            print('❌ Não foi possível abrir a câmera')
            return 1

    # K utilizado (pode ser reescalado após ler o 1º frame)
    K_use = K.copy()
    scaled_info = ""

    frames_done = 0
    while True:
        if picam2 is not None:
            frm = picam2.capture_array()
            if frm is None:
                time.sleep(0.01)
                continue
            frm = np.ascontiguousarray(frm, dtype=np.uint8)
            # Conversão conforme o formato escolhido
            if args.pixfmt == 'RGB888':
                frame = cv2.cvtColor(frm, cv2.COLOR_RGB2BGR)
            else:
                # XRGB8888 => descartar canal X e obter RGB
                if frm.ndim == 3 and frm.shape[2] == 4:
                    rgb = frm[:, :, 1:4]
                    frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                else:
                    # fallback seguro
                    frame = frm.copy()
        else:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            frame = np.ascontiguousarray(frame, dtype=np.uint8)

        # Se resolução de captura for diferente da usada na calibração, reescala K
        h, w = frame.shape[:2]
        cw, ch = calib_size
        if cw > 0 and ch > 0 and (w != cw or h != ch):
            sx = w / float(cw)
            sy = h / float(ch)
            K_scaled = K.copy()
            K_scaled[0, 0] *= sx  # fx
            K_scaled[1, 1] *= sy  # fy
            K_scaled[0, 2] *= sx  # cx
            K_scaled[1, 2] *= sy  # cy
            K_use = K_scaled
            scaled_info = f"[K escalado {sx:.3f}x{sy:.3f}]"
        else:
            K_use = K
            scaled_info = ""

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        vis = frame.copy()
        det_count = 0
        if args.detector == 'opencv':
            if detector is not None:
                corners, ids, _ = detector.detectMarkers(gray)
            else:
                corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=det_params)
            if ids is not None and len(ids) > 0:
                det_count = len(ids)
                try:
                    aruco.drawDetectedMarkers(vis, corners, ids)
                except Exception:
                    pass
                # Estima pose para cada tag
                for c in corners:
                    rvec, tvec, _ = aruco.estimatePoseSingleMarkers(c, tag_size_m, K_use, D)
                    if rvec is not None and tvec is not None:
                        rvec = rvec.reshape(-1, 3)[0]
                        tvec = tvec.reshape(-1, 3)[0]
                        if not args.no_axes:
                            try:
                                cv2.drawFrameAxes(vis, K_use, D, rvec, tvec, tag_size_m * 0.5)
                            except Exception:
                                pass
                        x, y = int(c[0][:, 0].mean()), int(c[0][:, 1].mean())
                        txt = f"x:{tvec[0]*100:.1f}cm y:{tvec[1]*100:.1f}cm z:{tvec[2]*100:.1f}cm"
                        cv2.putText(vis, txt, (x - 60, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            # pupil_apriltags path
            try:
                results = pupil_detector.detect(gray, estimate_tag_pose=True, camera_params=(K_use[0,0], K_use[1,1], K_use[0,2], K_use[1,2]), tag_size=tag_size_m)
            except Exception as e:
                results = []
            det_count = len(results)
            for r in results:
                # desenhar caixa
                try:
                    pts = r.corners.astype(int)
                    for j in range(4):
                        cv2.line(vis, tuple(pts[j]), tuple(pts[(j+1)%4]), (0,255,0), 2)
                    cxy = tuple(r.center.astype(int))
                    cv2.circle(vis, cxy, 3, (0,0,255), -1)
                except Exception:
                    pass
                # pose (r.pose_R, r.pose_t) em metros
                if r.pose_t is not None:
                    tvec = r.pose_t.reshape(-1)
                    txt = f"x:{tvec[0]*100:.1f}cm y:{tvec[1]*100:.1f}cm z:{tvec[2]*100:.1f}cm"
                    cv2.putText(vis, txt, (int(r.center[0])-60, int(r.center[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

        # Info de status
        if scaled_info:
            cv2.putText(vis, scaled_info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if args.no_window:
            # Rodar headless: apenas report básico no console
            print(f"Detecções: {det_count}")
        else:
            cv2.imshow('AprilTag Pose', vis)
            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                break

        frames_done += 1
        # Se pediu para salvar o último frame anotado, mantenha em memória
        last_vis = vis

        if args.frames and frames_done >= int(args.frames):
            break

    if cap is not None:
        cap.release()
    if picam2 is not None:
        try:
            picam2.stop()
            picam2.close()
        except Exception:
            pass
    # Salva o último frame anotado (modo live) se solicitado
    try:
        if args.save_out:
            if 'last_vis' in locals() and last_vis is not None:
                cv2.imwrite(args.save_out, last_vis)
    except Exception:
        pass
    # Em modo headless (--no-window) ou com builds headless do OpenCV, destruir janelas pode não estar implementado
    if not args.no_window:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
