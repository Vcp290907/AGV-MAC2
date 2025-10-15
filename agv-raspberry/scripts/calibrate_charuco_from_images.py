#!/usr/bin/env python3
"""
Calibração da câmera usando ChArUco a partir de imagens salvas (JPG/PNG).

Uso:
  python3 calibrate_charuco_from_images.py --images ./charuco_capturas --out camera_calib_charuco.json \
      --squares-x 5 --squares-y 7 --square-mm 40 --marker-mm 20 --dict DICT_4X4_50

Notas:
- Recomendado 20–30 imagens bem variadas (ângulo, distância, cobertura dos cantos).
- Suporta OpenCV com APIs novas (ArucoDetector) e antigas.
"""

import os
import glob
import json
import argparse
import numpy as np
import cv2


def get_aruco_objects(dict_name="DICT_4X4_50"):
    aruco = cv2.aruco
    DICT = getattr(aruco, dict_name)
    dictionary = aruco.getPredefinedDictionary(DICT)
    try:
        det_params = aruco.DetectorParameters()
    except AttributeError:
        det_params = aruco.DetectorParameters_create()
    try:
        detector = aruco.ArucoDetector(dictionary, det_params)
    except Exception:
        detector = None
    return aruco, dictionary, det_params, detector


def build_charuco_board(squares_x=5, squares_y=7, square_len_m=0.04, marker_len_m=0.02, dict_name="DICT_4X4_50"):
    aruco, dictionary, _, _ = get_aruco_objects(dict_name)
    try:
        board = aruco.CharucoBoard_create(squares_x, squares_y, square_len_m, marker_len_m, dictionary)
    except AttributeError:
        board = aruco.CharucoBoard((squares_x, squares_y), square_len_m, marker_len_m, dictionary)
    return board


def detect_charuco(gray, dictionary, det_params, detector, board):
    aruco = cv2.aruco
    if detector is not None:
        corners, ids, _ = detector.detectMarkers(gray)
    else:
        corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=det_params)

    if ids is None or len(ids) == 0:
        return None, None, corners, ids

    # Refinement pode causar segfault em alguns builds ARM do OpenCV 4.5/4.6 —
    # vamos deixar opcional e controlado via argumento.
    # (A chamada será feita no main se --refine estiver ativo.)

    retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(corners, ids, gray, board)
    if retval <= 0:
        return None, None, corners, ids
    return charuco_corners, charuco_ids, corners, ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=str, required=True, help="Pasta com imagens (JPG/PNG)")
    ap.add_argument("--out", type=str, default="camera_calib_charuco.json")
    ap.add_argument("--dict", type=str, default="DICT_4X4_50")
    ap.add_argument("--squares-x", type=int, default=5)
    ap.add_argument("--squares-y", type=int, default=7)
    ap.add_argument("--square-mm", type=float, default=40.0)
    ap.add_argument("--marker-mm", type=float, default=20.0)
    ap.add_argument("--min-corners", type=int, default=8, help="Mínimo de cantos ChArUco por imagem")
    ap.add_argument("--max-images", type=int, default=0, help="Limitar número de imagens (0 = sem limite)")
    ap.add_argument("--annotate-out", type=str, default="", help="Se definido, salva imagens anotadas nesta pasta")
    ap.add_argument("--verbose", action="store_true", help="Exibir contagem de cantos por imagem")
    ap.add_argument("--force-legacy", action="store_true", help="Força usar aruco.detectMarkers (evitar ArucoDetector)")
    ap.add_argument("--max-width", type=int, default=0, help="Redimensiona imagens para largura máxima (0 = sem redimensionar)")
    ap.add_argument("--no-draw", action="store_true", help="Não desenha/Salva anotações (mais estável em alguns ambientes)")
    ap.add_argument("--refine", action="store_true", help="Ativa refineDetectedMarkers (pode causar segfault em alguns builds)")
    ap.add_argument("--method", type=str, choices=["safe", "aruco", "markers"], default="safe",
                    help="'safe' usa cv2.calibrateCamera com pontos ChArUco (evita segfault); 'aruco' usa calibrateCameraCharuco")
    args = ap.parse_args()

    try:
        cv2.setNumThreads(1)
    except Exception:
        pass

    square_len_m = args.square_mm / 1000.0
    marker_len_m = args.marker_mm / 1000.0

    aruco, dictionary, det_params, detector = get_aruco_objects(args.dict)
    if args.force_legacy:
        detector = None
    board = build_charuco_board(args.squares_x, args.squares_y, square_len_m, marker_len_m, args.dict)

    patterns = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(args.images, p)))
    files = sorted(files)
    if not files:
        print(f"❌ Nenhuma imagem encontrada em {args.images}")
        return 1

    print(f"🖼️ Encontradas {len(files)} imagens em {args.images}")

    # Pasta para anotações
    if args.annotate_out:
        os.makedirs(args.annotate_out, exist_ok=True)

    all_corners = []  # lista de cantos ChArUco (para método aruco/safe)
    all_ids = []      # lista de ids ChArUco (para método aruco/safe)
    markers_objpoints = []  # para método markers: lista por imagem de objpoints (N,3)
    markers_imgpoints = []  # para método markers: lista por imagem de imgpoints (N,2)
    img_size = None
    good = 0

    count = 0
    # Desabilitar otimizações que podem causar instabilidade em alguns builds ARM
    try:
        cv2.setUseOptimized(False)
    except Exception:
        pass

    for fp in files:
        img = cv2.imread(fp)
        if img is None:
            print(f"⚠️ Não foi possível ler {fp}")
            continue
        # Redimensionar se solicitado
        if args.max_width and img.shape[1] > int(args.max_width):
            scale = float(args.max_width) / float(img.shape[1])
            new_w = int(img.shape[1] * scale)
            new_h = int(img.shape[0] * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        img = np.ascontiguousarray(img, dtype=np.uint8)
        h, w = img.shape[:2]
        if img_size is None:
            img_size = (w, h)
        else:
            if (w, h) != (img_size[0], img_size[1]):
                print(f"⚠️ Tamanho diferente em {os.path.basename(fp)} ({w}x{h}), esperado {img_size[0]}x{img_size[1]} — ignorando")
                continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detecção base
        aruco = cv2.aruco
        if detector is not None:
            corners, ids, _ = detector.detectMarkers(gray)
        else:
            corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=det_params)

        charuco_corners, charuco_ids = None, None
        if ids is not None and len(ids) > 0:
            # Método markers: coletar correspondências 2D-3D de cantos dos marcadores
            if args.method == "markers":
                # Montar mapa id->objPoints(4,3)
                try:
                    board_ids = np.array(board.ids).reshape(-1)
                    board_obj = [np.array(op, dtype=np.float32).reshape(-1, 3) for op in board.objPoints]
                except Exception:
                    # fallback genérico
                    board_ids = np.array(board.ids).reshape(-1)
                    board_obj = [np.asarray(op, dtype=np.float32).reshape(-1, 3) for op in board.objPoints]
                id_to_obj = {int(i): board_obj[k] for k, i in enumerate(board_ids)}

                pts2d_list = []
                pts3d_list = []
                for mk, mid in zip(corners, ids.reshape(-1)):
                    mid = int(mid)
                    if mid in id_to_obj:
                        # 'mk' tem shape (1,4,2)
                        pts2d = np.ascontiguousarray(mk.reshape(4, 2), dtype=np.float32)
                        pts3d = id_to_obj[mid]
                        if pts2d.shape[0] == 4 and pts3d.shape[0] == 4:
                            pts2d_list.append(pts2d)
                            pts3d_list.append(pts3d)
                if len(pts2d_list) > 0:
                    markers_imgpoints.append(np.vstack(pts2d_list))
                    markers_objpoints.append(np.vstack(pts3d_list))

            else:
                # Refine opcional
                if args.refine:
                    try:
                        aruco.refineDetectedMarkers(gray, board, corners, ids, rejectedCorners=None)
                    except Exception:
                        pass
                # Interpolar cantos ChArUCo
                try:
                    retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(corners, ids, gray, board)
                    if retval <= 0:
                        charuco_corners, charuco_ids = None, None
                except Exception:
                    charuco_corners, charuco_ids = None, None

        # Anotar e opcionalmente salvar
        if (args.verbose or args.annotate_out) and not args.no_draw:
            vis = img.copy()
            try:
                if ids is not None and corners is not None and len(corners) > 0:
                    cv2.aruco.drawDetectedMarkers(vis, corners, ids)
                if charuco_corners is not None and charuco_ids is not None and len(charuco_corners) > 0:
                    cv2.aruco.drawDetectedCornersCharuco(vis, charuco_corners, charuco_ids, (0, 255, 0))
            except Exception:
                pass
            if args.verbose:
                cnt = 0 if charuco_ids is None else int(len(charuco_ids))
                print(f"• {os.path.basename(fp)}: {cnt} cantos ChArUco")
            if args.annotate_out:
                outp = os.path.join(args.annotate_out, os.path.basename(fp))
                try:
                    cv2.imwrite(outp, vis)
                except Exception:
                    pass

        if args.method == "markers":
            if len(markers_imgpoints) > good:
                good += 1
            else:
                print(f"⚠️ Detecção insuficiente (markers) em {os.path.basename(fp)}")
        else:
            if charuco_corners is not None and charuco_ids is not None and len(charuco_ids) >= int(args.min_corners):
                # Garantir tipos e contiguidade que o OpenCV espera
                cc = np.ascontiguousarray(charuco_corners, dtype=np.float32)
                ii = np.ascontiguousarray(charuco_ids, dtype=np.int32)
                all_corners.append(cc)
                all_ids.append(ii)
                good += 1
            else:
                print(f"⚠️ Detecção insuficiente em {os.path.basename(fp)}")

        count += 1
        if args.max_images and count >= int(args.max_images):
            break

    if good < 10:
        print(f"⚠️ Poucas imagens válidas ({good}). Recomenda-se >= 10-20.")

    if good == 0:
        print("❌ Nenhuma imagem com detecção suficiente. Verifique iluminação, foco e se a folha é 5x7 com 40mm/20mm.")
        return 2

    print("🧮 Calibrando...")
    if args.method == "aruco":
        # Método original (pode dar segfault em alguns builds)
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
            retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharucoExtended(
                charucoCorners=all_corners,
                charucoIds=all_ids,
                board=board,
                imageSize=img_size,
                cameraMatrix=None,
                distCoeffs=None
            )
    elif args.method == "safe":
        # Método seguro: mapeia cantos ChArUco para cv2.calibrateCamera
        # Para cada imagem: ids -> índices nos cantos 3D (board.chessboardCorners)
        objpoints = []  # lista de (N,3)
        imgpoints = []  # lista de (N,2)
        chess3d = None
        try:
            chess3d = np.array(board.getChessboardCorners(), dtype=np.float32)
        except Exception:
            try:
                chess3d = np.array(board.chessboardCorners, dtype=np.float32)
            except Exception:
                chess3d = np.asarray(board.getChessboardCorners(), dtype=np.float32)

        for cc, ii in zip(all_corners, all_ids):
            if cc is None or ii is None:
                continue
            pts2d = np.ascontiguousarray(cc.reshape(-1, 2), dtype=np.float32)
            ids1d = np.ascontiguousarray(ii.reshape(-1), dtype=np.int32)
            # Filtrar ids válidos no range do tabuleiro
            valid = (ids1d >= 0) & (ids1d < chess3d.shape[0])
            ids1d = ids1d[valid]
            pts2d = pts2d[valid]
            if len(ids1d) >= int(args.min_corners):
                objp = np.ascontiguousarray(chess3d[ids1d], dtype=np.float32)
                objpoints.append(objp)
                imgpoints.append(pts2d)

        if len(objpoints) == 0:
            print("❌ Falha ao montar pontos para calibracao segura.")
            return 3

        # Calibração padrão pinhole
        flags = 0
        retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objectPoints=objpoints,
            imagePoints=imgpoints,
            imageSize=img_size,
            cameraMatrix=None,
            distCoeffs=None,
            flags=flags
        )
    else:
        # Método markers: usa apenas cantos dos marcadores detectados
        if len(markers_objpoints) == 0 or len(markers_imgpoints) == 0:
            print("❌ Nenhum ponto (markers) acumulado.")
            return 4
        retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objectPoints=markers_objpoints,
            imagePoints=markers_imgpoints,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
