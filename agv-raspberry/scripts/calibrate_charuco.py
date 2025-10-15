#!/usr/bin/env python3
"""
Calibração da câmera usando ChArUco (tabuleiro com quadrados 40mm e marcadores 20mm)

Passos de uso:
 1) Imprima a folha ChArUco (A4) em 100% (sem escala). Confirme: quadrado = 40mm, marcador = 20mm.
 2) Conecte a câmera (index padrão 0).
 3) Rode este script. Mostrará uma janela com a detecção das marcas.
 4) Pressione ESPAÇO para capturar uma amostra boa (varie ângulo, distância e cobertura dos cantos).
 5) Após 20-30 amostras, pressione 'c' para calibrar.
 6) O resultado será salvo em camera_calib_charuco.json.

Observação: Este script usa o modelo PINHOLE padrão do OpenCV (k1..k5). Para lentes fisheye muito fortes,
é possível que um script com o modelo fisheye seja mais adequado. Se necessário, podemos criar um específico.
"""

import json
import time
import argparse
import numpy as np
import cv2

# Suporte opcional a Picamera2 (recomendado no Raspberry Pi)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False


def get_aruco_objects(dict_name="DICT_4X4_50"):
    aruco = cv2.aruco
    # Dicionário
    DICT = getattr(aruco, dict_name)
    dictionary = aruco.getPredefinedDictionary(DICT)

    # Parâmetros do detector (compatíveis com versões antigas e novas do OpenCV)
    try:
        det_params = aruco.DetectorParameters()
    except AttributeError:
        det_params = aruco.DetectorParameters_create()

    # Detector unificado (OpenCV >= 4.7)
    detector = None
    try:
        detector = aruco.ArucoDetector(dictionary, det_params)
    except Exception:
        detector = None

    return aruco, dictionary, det_params, detector


def build_charuco_board(squares_x=5, squares_y=7, square_len_m=0.04, marker_len_m=0.02, dict_name="DICT_4X4_50"):
    aruco, dictionary, _, _ = get_aruco_objects(dict_name)
    # API antiga e nova
    try:
        board = aruco.CharucoBoard_create(squares_x, squares_y, square_len_m, marker_len_m, dictionary)
    except AttributeError:
        board = aruco.CharucoBoard((squares_x, squares_y), square_len_m, marker_len_m, dictionary)
    return board


def detect_charuco_corners(gray, dictionary, det_params, detector, board):
    aruco = cv2.aruco
    if detector is not None:
        corners, ids, _ = detector.detectMarkers(gray)
    else:
        corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=det_params)

    if ids is None or len(ids) == 0:
        return None, None, corners, ids

    # Refinar e interpolar cantos ChArUco
    try:
        aruco.refineDetectedMarkers(gray, board, corners, ids, rejectedCorners=None)
    except Exception:
        pass

    retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(corners, ids, gray, board)
    if retval <= 0:
        return None, None, corners, ids
    return charuco_corners, charuco_ids, corners, ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera-index", type=int, default=0, help="Índice da câmera (default 0) [backend opencv]")
    ap.add_argument("--backend", type=str, default="auto", choices=["auto", "picam", "opencv"], help="Backend de captura: auto/picam/opencv")
    ap.add_argument("--width", type=int, default=1280, help="Largura do frame (preview)")
    ap.add_argument("--height", type=int, default=720, help="Altura do frame (preview)")
    ap.add_argument("--dict", type=str, default="DICT_4X4_50", help="Dicionário ArUco (ex: DICT_4X4_50)")
    ap.add_argument("--squares-x", type=int, default=5)
    ap.add_argument("--squares-y", type=int, default=7)
    ap.add_argument("--square-mm", type=float, default=40.0, help="Tamanho do quadrado em mm no papel")
    ap.add_argument("--marker-mm", type=float, default=20.0, help="Tamanho do marcador em mm no papel")
    ap.add_argument("--out", type=str, default="camera_calib_charuco.json")
    args = ap.parse_args()

    # Reduz threads do OpenCV para evitar race conditions em SBCs
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass

    square_len_m = args.square_mm / 1000.0
    marker_len_m = args.marker_mm / 1000.0

    aruco, dictionary, det_params, detector = get_aruco_objects(args.dict)
    board = build_charuco_board(args.squares_x, args.squares_y, square_len_m, marker_len_m, args.dict)

    cap = None
    picam2 = None
    use_picam = (args.backend == "picam") or (args.backend == "auto" and PICAMERA2_AVAILABLE)

    if use_picam and PICAMERA2_AVAILABLE:
        try:
            picam2 = Picamera2()
            cfg = picam2.create_preview_configuration(main={"format": 'RGB888', "size": (int(args.width), int(args.height))})
            picam2.configure(cfg)
            picam2.start()
        except Exception as e:
            print(f"⚠️ Falha ao iniciar Picamera2 ({e}). Tentando OpenCV...")
            picam2 = None

    if picam2 is None:
        cap = cv2.VideoCapture(args.camera_index)
        if args.width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(args.width))
        if args.height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(args.height))
        if not cap.isOpened():
            print("❌ Não foi possível abrir a câmera")
            return 1

    print("📷 Câmera aberta. Pressione ESPAÇO para capturar, 'c' para calibrar, 'q' para sair.")

    all_corners = []
    all_ids = []
    img_size = None

    while True:
        if picam2 is not None:
            frame = picam2.capture_array()
            if frame is None:
                time.sleep(0.02)
                continue
            # Picamera2 retorna RGB
            frame = np.ascontiguousarray(frame, dtype=np.uint8)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.02)
                continue
            frame = np.ascontiguousarray(frame, dtype=np.uint8)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img_size = (frame.shape[1], frame.shape[0])

        charuco_corners, charuco_ids, corners, ids = detect_charuco_corners(gray, dictionary, det_params, detector, board)

        vis = frame.copy()
        # Desenhar apenas se houver detecções válidas
        if ids is not None and corners is not None and len(corners) > 0:
            try:
                cv2.aruco.drawDetectedMarkers(vis, corners, ids)
            except Exception:
                pass
        if charuco_corners is not None and charuco_ids is not None and len(charuco_corners) > 0:
            try:
                cv2.aruco.drawDetectedCornersCharuco(vis, charuco_corners, charuco_ids, (0, 255, 0))
            except Exception:
                pass

        cv2.putText(vis, f"Capturas: {len(all_corners)}  [SPACE]=capturar  [c]=calibrar  [q]=sair",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imshow("Calibracao ChArUco", vis)

        k = cv2.waitKey(1) & 0xFF
        if k == ord(' '):
            if charuco_corners is not None and charuco_ids is not None and len(charuco_ids) >= 8:
                all_corners.append(charuco_corners)
                all_ids.append(charuco_ids)
                print(f"✅ Amostra capturada (total {len(all_corners)})")
            else:
                print("⚠️ Detecção insuficiente de cantos ChArUco — tente outra pose")
        elif k == ord('c'):
            if len(all_corners) < 10:
                print("⚠️ Poucas amostras. Capture pelo menos 10-20.")
                continue
            print("🧮 Calibrando...")
            camera_matrix = np.zeros((3,3))
            dist_coeffs = np.zeros((1,5))
            try:
                retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
                    charucoCorners=all_corners,
                    charucoIds=all_ids,
                    board=board,
                    imageSize=img_size,
                    cameraMatrix=None,
                    distCoeffs=None
                )
            except AttributeError:
                # Fallback para versões mais antigas
                retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharucoExtended(
                    charucoCorners=all_corners,
                    charucoIds=all_ids,
                    board=board,
                    imageSize=img_size,
                    cameraMatrix=None,
                    distCoeffs=None
                )
            print(f"✅ Calibração concluída. Erro reprojeção: {retval:.4f}")

            data = {
                'image_width': img_size[0],
                'image_height': img_size[1],
                'camera_matrix': camera_matrix.tolist(),
                'dist_coeffs': dist_coeffs.tolist(),
                'reprojection_error': float(retval),
                'dict': args.dict,
                'charuco': {
                    'squares_x': args.squares_x,
                    'squares_y': args.squares_y,
                    'square_m': square_len_m,
                    'marker_m': marker_len_m
                }
            }
            with open(args.out, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Salvo em {args.out}")

        elif k == ord('q'):
            break

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
