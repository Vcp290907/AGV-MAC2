#!/usr/bin/env python3
"""
Navegação Seguindo Linha Preta com PID
Integra detecção de linha com controle de motores e QR codes
"""

import time
import os
import threading
import platform
import numpy as np
from line_detector import LineDetector
from navigation_basic import BasicNavigation
from config import get_esp32_port, NAVIGATION_CONFIG
import cv2

class LineFollowingNavigation:
    """Navegação que segue linha preta com detecção de QR codes"""

    def __init__(self, esp32_port=None, visual_feedback=False):
        self.esp32_port = esp32_port or get_esp32_port()

        # Componentes
        self.line_detector = LineDetector()  # Picamera2 não usa camera_id
        self.basic_nav = BasicNavigation(esp32_port=self.esp32_port)
        # QR detector removido - usaremos pyzbar diretamente no frame da linha

        # Estado da navegação
        self.following_line = False
        # Velocidades e ganho vindos de config para tuning rápido
        lf_cfg = NAVIGATION_CONFIG.get('line_following', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
        self.speed_base = int(lf_cfg.get('speed_base', 50))
        self.speed_min = int(lf_cfg.get('speed_min', 20))
        self.speed_max = int(lf_cfg.get('speed_max', 70))
        # Ganho adicional para a correção de direção (escala o steering do detector)
        self.steering_gain = float(lf_cfg.get('steering_gain', 1.6))

        # Detecção de QR codes
        self.qr_detected_recently = False
        self.current_subcorredor = None  # Subcorredor atual detectado

        # Feedback visual opcional
        self.visual_feedback = visual_feedback
        self.visual_window_name = "AGV - Seguimento de Linha"
        self.current_frame = None
        self.status_info = {
            'velocidade': 0,
            'direcao': 'parado',
            'erro_pixels': 0,
            'correcao': 0.0,
            'qr_detectado': False,
            'linha_detectada': False,
            'confianca': 0.0,
            'subcorredor': None,
            'qr_texto': None
        }

        # Estado de leitura de QR para controlar retorno ao modo normal
        self.last_qr_text = None
        self.last_qr_time = 0.0
        # Controle de comportamento em quadrado verde
        self.green_since_time = None
        self.last_green_stop_time = 0.0

        # Inicializar detector OpenCV como fallback
        try:
            self.cv_qr_detector = cv2.QRCodeDetector()
        except Exception:
            self.cv_qr_detector = None

        # Threading/controle de loop
        self.navigation_thread = None
        self.stop_event = threading.Event()
        self.intersection_detected = False
        # Snapshots
        self.last_snapshot_time = 0.0
        self.snapshot_cooldown = 0.25  # seg entre snapshots de falha
        # Pasta 'captures' ao lado deste arquivo, portátil entre Windows/Pi
        self.snapshots_dir = os.path.join(os.path.dirname(__file__), 'captures')

    def _decode_qr_multi(self, img_bgr):
        """Tentar decodificar QR usando múltiplos pré-processamentos e retificação.
        Retorna lista de dicts: {'bbox': (x,y,w,h), 'data': '...'}
        """
        results = []
        h_img, w_img = img_bgr.shape[:2]

        # Importar pyzbar se disponível
        try:
            from pyzbar.pyzbar import decode as zbar_decode
        except Exception:
            zbar_decode = None

        def unsharp(image_gray):
            try:
                blur = cv2.GaussianBlur(image_gray, (0, 0), 1.0)
                sharp = cv2.addWeighted(image_gray, 1.5, blur, -0.5, 0)
                return sharp
            except Exception:
                return image_gray

        def add_quiet_zone(image_gray, border=16, invert=False):
            try:
                bordered = cv2.copyMakeBorder(
                    image_gray, border, border, border, border,
                    cv2.BORDER_CONSTANT, value=255 if not invert else 0
                )
                return bordered
            except Exception:
                return image_gray

        def try_decode_with_pyzbar(img_variant, bbox_hint=None):
            local = []
            if zbar_decode is None:
                return local
            try:
                # pyzbar aceita BGR/GRAY; convertemos para otimizar
                if len(img_variant.shape) == 3:
                    var_gray = cv2.cvtColor(img_variant, cv2.COLOR_BGR2GRAY)
                else:
                    var_gray = img_variant

                # Tentar direto
                qr_codes = zbar_decode(var_gray)
                if not qr_codes:
                    # Tentar com quiet zone (bordas brancas) e versão invertida
                    qz = add_quiet_zone(var_gray, border=24, invert=False)
                    qr_codes = zbar_decode(qz)
                if not qr_codes:
                    inv = cv2.bitwise_not(var_gray)
                    qr_codes = zbar_decode(inv) or zbar_decode(add_quiet_zone(inv, border=24, invert=True))

                for res in qr_codes or []:
                    x, y, w, h = (
                        res.rect.left,
                        res.rect.top,
                        res.rect.width,
                        res.rect.height,
                    )
                    # Se vier retificado, bbox_hint substitui
                    if bbox_hint is not None:
                        x, y, w, h = bbox_hint
                    data_txt = res.data.decode('utf-8') if res.data else ''
                    local.append({'bbox': (x, y, w, h), 'data': data_txt})
            except Exception:
                return local
            return local

        def build_variants(img):
            variants = []
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            except Exception:
                gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            variants.append(('color', img))
            variants.append(('gray', gray))

            # CLAHE
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray_clahe = clahe.apply(gray)
                variants.append(('clahe', gray_clahe))
            except Exception:
                pass

            # Unsharp
            try:
                usharp = unsharp(gray)
                variants.append(('unsharp', usharp))
            except Exception:
                pass

            # Adaptive/otsu
            try:
                blur = cv2.GaussianBlur(gray, (3, 3), 0)
                adapt = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                              cv2.THRESH_BINARY, 11, 2)
                variants.append(('adaptive', adapt))
                _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                variants.append(('otsu', otsu))
            except Exception:
                pass

            # Escalas
            try:
                up1 = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
                variants.append(('gray_up1.5', up1))
                up2 = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                variants.append(('gray_up2.0', up2))
            except Exception:
                pass

            return variants

        # 1) Tentar pyzbar nas variantes comuns
        try:
            for _name, v in build_variants(img_bgr):
                decoded = try_decode_with_pyzbar(v)
                if decoded:
                    return decoded
        except Exception:
            pass

        # 2) Tentar detectar contorno com OpenCV, retificar e decodificar
        try:
            if self.cv_qr_detector is not None:
                ok, points = self.cv_qr_detector.detect(img_bgr)
                if ok and points is not None and len(points) >= 1:
                    # Pegar o maior quadrilátero
                    best = None
                    best_area = 0
                    for poly in points:
                        pts = poly.reshape(-1, 2).astype(np.float32)
                        area = cv2.contourArea(pts)
                        if area > best_area:
                            best, best_area = pts, area
                    if best is not None and best.shape[0] >= 4:
                        # Ordenar cantos: tl,tr,br,bl
                        def order_pts(pts):
                            s = pts.sum(axis=1)
                            diff = np.diff(pts, axis=1)
                            tl = pts[np.argmin(s)]
                            br = pts[np.argmax(s)]
                            tr = pts[np.argmin(diff)]
                            bl = pts[np.argmax(diff)]
                            return np.array([tl, tr, br, bl], dtype=np.float32)
                        quad = order_pts(best)
                        (tl, tr, br, bl) = quad
                        widthA = np.linalg.norm(br - bl)
                        widthB = np.linalg.norm(tr - tl)
                        maxW = int(max(widthA, widthB))
                        heightA = np.linalg.norm(tr - br)
                        heightB = np.linalg.norm(tl - bl)
                        maxH = int(max(heightA, heightB))
                        dst = np.array([[0,0],[maxW-1,0],[maxW-1,maxH-1],[0,maxH-1]], dtype=np.float32)
                        M = cv2.getPerspectiveTransform(quad, dst)
                        warped = cv2.warpPerspective(img_bgr, M, (maxW, maxH))

                        # bbox_hint baseado no bounding rect original
                        xs = [int(p[0]) for p in best]
                        ys = [int(p[1]) for p in best]
                        bx, by, bw, bh = min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)

                        for _name, v in build_variants(warped):
                            decoded = try_decode_with_pyzbar(v, bbox_hint=(bx, by, bw, bh))
                            if decoded:
                                return decoded
        except Exception:
            pass

        # 3) Fallback: OpenCV detectAndDecodeMulti e detectAndDecode
        try:
            if self.cv_qr_detector is not None:
                data_list, points_list, _ = self.cv_qr_detector.detectAndDecodeMulti(img_bgr)
                if data_list:
                    for data, pts in zip(data_list, points_list):
                        if not data:
                            continue
                        xs = [int(p[0]) for p in pts]
                        ys = [int(p[1]) for p in pts]
                        x, y, w, h = min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)
                        results.append({'bbox': (x, y, w, h), 'data': data})
                    if results:
                        return results

                data, points, _ = self.cv_qr_detector.detectAndDecode(img_bgr)
                if data:
                    if points is not None and len(points) >= 4:
                        pts = points[0] if len(points.shape) == 3 else points
                        xs = [int(p[0]) for p in pts]
                        ys = [int(p[1]) for p in pts]
                        x, y, w, h = min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)
                    else:
                        x, y, w, h = 0, 0, w_img, h_img
                    results.append({'bbox': (x, y, w, h), 'data': data})
                    return results
        except Exception:
            pass

        return results

    def enable_visual_feedback(self):
        """Ativar feedback visual"""
        self.visual_feedback = True
        # Tentar criar a janela imediatamente (se houver DISPLAY)
        try:
            import os
            if os.environ.get('DISPLAY'):
                cv2.namedWindow(self.visual_window_name, cv2.WINDOW_NORMAL)
        except Exception:
            pass
        print("👁️ Feedback visual ativado")
        print("ℹ️ Dica: inicie o teste (opção 1) para ver o vídeo em tempo real.")

    def disable_visual_feedback(self):
        """Desativar feedback visual"""
        self.visual_feedback = False
        try:
            cv2.destroyWindow(self.visual_window_name)
        except:
            pass
        print("👁️ Feedback visual desativado")

    def _scan_shelf_qr_secondary_camera(self, camera_index=0, duration_s=3.0, debug=False, debug_dir=None, debug_prefix='shelf_qr'):
        """Usar segunda câmera para varrer e ler QR codes na estante, sem conflitar com a câmera principal.
        Retorna lista de dicts {bbox, data} (únicos por texto). Se debug=True, salva imagem anotada e .txt com posições.
        """
        # Usar o CameraManager compartilhado para evitar conflitos com Picamera2 e threads internas
        try:
            from qr_reader_opencv_only import get_camera_manager
        except Exception as e:
            print(f"❌ CameraManager indisponível para câmera secundária: {e}")
            return []

        unique = {}
        best_frame_bgr = None
        last_frame_bgr = None  # manter último frame para salvar mesmo sem QR
        best_results = []

        try:
            cam_mgr = get_camera_manager(camera_index)
            if not cam_mgr.initialize():
                print("❌ Falha ao inicializar CameraManager para câmera secundária")
                return []

            t0 = time.time()
            while time.time() - t0 < float(duration_s):
                frame = cam_mgr.capture_frame()
                if frame is None:
                    time.sleep(0.03)
                    continue
                # frame vem em RGB, converter para BGR
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                last_frame_bgr = frame_bgr
                results = self._decode_qr_multi(frame_bgr)
                # Manter o melhor frame (maior número de QRs lidos nesta captura)
                if results and len(results) > len(best_results):
                    best_results = results
                    best_frame_bgr = frame_bgr.copy()
                for r in results or []:
                    txt = r.get('data')
                    if not txt:
                        continue
                    if txt not in unique:
                        unique[txt] = r
                time.sleep(0.02)
        except Exception as e:
            print(f"⚠️ Erro na varredura com câmera secundária: {e}")

        # Salvar imagem anotada SEMPRE; TXT opcional se debug=True (grid 2x2 com quadrantes)
        try:
            frame_to_use = best_frame_bgr if best_frame_bgr is not None else last_frame_bgr
            if frame_to_use is not None:
                save_dir = debug_dir or self.snapshots_dir
                os.makedirs(save_dir, exist_ok=True)
                ts = int(time.time()*1000)
                out_img = frame_to_use.copy()
                H, W = out_img.shape[:2]
                cx_mid, cy_mid = W//2, H//2
                # desenhar linhas do grid 2x2
                cv2.line(out_img, (cx_mid, 0), (cx_mid, H-1), (0, 255, 255), 2)
                cv2.line(out_img, (0, cy_mid), (W-1, cy_mid), (0, 255, 255), 2)
                # helper de quadrante
                def quadrant_for_bbox(bx, by, bw, bh):
                    c_x, c_y = bx + bw//2, by + bh//2
                    if c_y < cy_mid and c_x < cx_mid:
                        return 'TopLeft', (c_x, c_y)
                    if c_y < cy_mid and c_x >= cx_mid:
                        return 'TopRight', (c_x, c_y)
                    if c_y >= cy_mid and c_x < cx_mid:
                        return 'BottomLeft', (c_x, c_y)
                    return 'BottomRight', (c_x, c_y)
                # Anotar bbox/labels (se houver resultados)
                if best_results:
                    for r in best_results:
                        bx, by, bw, bh = r.get('bbox', (0,0,0,0))
                        data = r.get('data', '')
                        quad, _ = quadrant_for_bbox(bx, by, bw, bh)
                        cv2.rectangle(out_img, (bx, by), (bx+bw, by+bh), (0, 255, 0), 2)
                        label = f"{quad}: {data[:48]}" if data else quad
                        font_scale = max(0.6, min(2.0, W / 1280.0))
                        thickness = 2 if W <= 1920 else 3
                        cv2.putText(out_img, label, (bx, max(30, by-10)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,255,0), thickness)
                else:
                    # indicar que nenhum QR foi detectado
                    cv2.putText(out_img, 'Nenhum QR detectado', (20, max(40, cy_mid-10)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)
                img_path = os.path.join(save_dir, f"{debug_prefix}_{ts}.png")
                cv2.imwrite(img_path, out_img)
                self.last_shelf_qr_image_path = img_path
                print(f"🖼️ Imagem da estante anotada salva: {img_path}")
                # TXT somente se debug=True
                if debug:
                    txt_path = os.path.join(save_dir, f"{debug_prefix}_{ts}.txt")
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(f"Shelf QR scan at {ts}\n")
                        for idx, r in enumerate(best_results):
                            bx, by, bw, bh = r.get('bbox', (0,0,0,0))
                            data = r.get('data', '')
                            quad, center_pt = quadrant_for_bbox(bx, by, bw, bh)
                            f.write(f"{idx+1}. quadrant={quad}\tdata={data}\tbbox=({bx},{by},{bw},{bh})\tcenter=({center_pt[0]},{center_pt[1]})\n")
                    print(f"📝 Lista de QR (debug) salva: {txt_path}")
        except Exception as e:
            print(f"⚠️ Falha ao salvar imagem/TXT da estante: {e}")

        # anexar caminho da imagem anotada aos resultados
        results_list = list(unique.values())
        try:
            img_path = getattr(self, 'last_shelf_qr_image_path', None)
            if img_path:
                for r in results_list:
                    # não sobrescrever se já existir
                    if isinstance(r, dict) and 'image_path' not in r:
                        r['image_path'] = img_path
        except Exception:
            pass
        return results_list

    def update_visual_frame(self, frame, line_info=None):
        """Atualizar frame para display visual com interface aprimorada"""
        if not self.visual_feedback:
            return

        # Verificar se há display disponível
        import os
        if os.environ.get('DISPLAY') is None:
            if frame is not None:  # Só mostrar uma vez
                print("⚠️ Display não disponível - feedback visual desativado automaticamente")
                self.visual_feedback = False
            return

        if frame is None:
            return

        self.current_frame = frame.copy()

        # Desenhar elementos visuais aprimorados
        self._draw_visual_elements(line_info)

        # Adicionar painel de informações
        self._draw_info_panel(line_info)

        # Adicionar indicadores de status
        self._draw_status_indicators()

        # Mostrar imagem
        cv2.imshow(self.visual_window_name, self.current_frame)
        cv2.waitKey(1)  # Necessário para atualizar a janela

    def _ensure_snapshots_dir(self):
        try:
            import os
            os.makedirs(self.snapshots_dir, exist_ok=True)
        except Exception:
            pass

    def _save_snapshot(self, base_bgr, line_info, suffix):
        """Salvar uma imagem com overlays + ROI do QR (se houver).
        base_bgr: imagem BGR (ROI atual)
        line_info: dict com 'qr_codes' e 'green_square' para desenhar
        suffix: texto para compor nome (ex: 'qr_ok', 'qr_fail')
        """
        try:
            import os
            import datetime as dt
            self._ensure_snapshots_dir()

            # Copiar frame e desenhar overlays mínimos (quadrado verde + QRs)
            img = base_bgr.copy()
            gs = (line_info or {}).get('green_square') or {}
            if gs.get('detected'):
                x, y, w, h = gs.get('bbox', (0, 0, 0, 0))
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(img, 'GREEN', (x, max(15, y-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

            for qr in (line_info or {}).get('qr_codes', []) or []:
                qx, qy, qw, qh = qr.get('bbox', (0,0,0,0))
                data_txt = qr.get('data', '')
                cv2.rectangle(img, (qx, qy), (qx+qw, qy+qh), (255, 0, 0), 2)
                cv2.putText(img, data_txt[:32], (qx, max(15, qy-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)

            ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            base_name = f"{ts}_{suffix}"
            path_full = os.path.join(self.snapshots_dir, base_name + "_roi.jpg")
            cv2.imwrite(path_full, img)

            # Salvar a ROI do QR principal, se houver
            if (line_info or {}).get('qr_codes'):
                qx, qy, qw, qh = line_info['qr_codes'][0].get('bbox', (0,0,0,0))
                if qw > 0 and qh > 0:
                    qr_crop = base_bgr[qy:qy+qh, qx:qx+qw].copy()
                    path_qr = os.path.join(self.snapshots_dir, base_name + "_qr.jpg")
                    cv2.imwrite(path_qr, qr_crop)

            # Também salvar um txt com conteúdo, se houver
            data_txt = None
            if (line_info or {}).get('qr_codes'):
                data_txt = line_info['qr_codes'][0].get('data')
            if data_txt:
                with open(os.path.join(self.snapshots_dir, base_name + ".txt"), 'w', encoding='utf-8') as f:
                    f.write(str(data_txt))
        except Exception as e:
            print(f"⚠️ Falha ao salvar snapshot: {e}")

    def _draw_visual_elements(self, line_info):
        """Desenhar elementos visuais na câmera"""
        height, width = self.current_frame.shape[:2]

        # 1. Linha central da câmera (branca fina)
        cv2.line(self.current_frame, (width//2, 0), (width//2, height), (255, 255, 255), 1)

        # 2. Área de detecção (ROI) - como exibimos apenas a ROI, destacar quadro inteiro
        cv2.rectangle(self.current_frame, (0, 0), (width, height), (0, 255, 0), 2)

        # 3. Grade de referência (linhas pontilhadas)
        self._draw_dashed_line((0, height//2), (width, height//2), (100, 100, 100), 1, 10, 5)

        # 4. Elementos da linha detectada
        if line_info and line_info.get('detected', False):
            center = line_info.get('center', width//2)
            confidence = line_info.get('confidence', 0.0)
            steering = line_info.get('steering_correction', 0.0)

            # Cor baseada na confiança
            if confidence > 0.8:
                line_color = (0, 255, 0)  # Verde - boa detecção
            elif confidence > 0.5:
                line_color = (0, 255, 255)  # Amarelo - detecção média
            else:
                line_color = (0, 165, 255)  # Laranja - detecção fraca

            # Centro da linha detectada (círculo maior)
            cv2.circle(self.current_frame, (center, height//2), 8, line_color, -1)
            cv2.circle(self.current_frame, (center, height//2), 12, line_color, 2)

            # Bounding box da linha (se disponível)
            if 'x' in line_info and 'w' in line_info:
                x, y, w, h = line_info['x'], line_info['y'], line_info['w'], line_info['h']
                cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), line_color, 2)

            # Indicador de direção (seta)
            self._draw_direction_arrow(center, height//2, steering, line_color)

            # 5. Indicador de zona morta central
            deadzone_size = 20
            cv2.rectangle(self.current_frame,
                         (width//2 - deadzone_size, height//2 - deadzone_size),
                         (width//2 + deadzone_size, height//2 + deadzone_size),
                         (255, 255, 255), 1)

        # 6. Desenhar candidatos e quadrado verde detectado (se houver)
        if line_info and 'green_square' in line_info:
            gs = line_info['green_square']
            # Candidatos em amarelo
            for cand in gs.get('candidates', [])[:5]:
                cx, cy, cw, ch = cand['bbox']
                cv2.rectangle(self.current_frame, (cx, cy), (cx+cw, cy+ch), (0, 255, 255), 1)
                cv2.putText(self.current_frame, f"v{cand.get('vertices','?')} r{cand.get('aspect',0):.2f}",
                           (cx, max(12, cy-4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,255), 1)

            if gs.get('detected'):
                x, y, w, h = gs['bbox']
                # Desenhar retângulo verde ao redor do quadrado detectado
                cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                # Desenhar ponto central
                center_x, center_y = gs['center']
                cv2.circle(self.current_frame, (center_x, center_y), 5, (0, 255, 0), -1)
                cv2.putText(self.current_frame, "QR AREA", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 7. Desenhar QR codes detectados (se houver)
        if line_info and 'qr_codes' in line_info and line_info['qr_codes']:
            for qr in line_info['qr_codes']:
                (qx, qy, qw, qh) = qr.get('bbox', (None, None, None, None))
                data_txt = qr.get('data', '')
                if None not in (qx, qy, qw, qh):
                    cv2.rectangle(self.current_frame, (qx, qy), (qx+qw, qy+qh), (255, 0, 0), 2)
                    cv2.putText(self.current_frame, f"QR: {data_txt[:28]}", (qx, max(15, qy-5)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    def _draw_direction_arrow(self, x, y, steering_correction, color):
        """Desenhar seta indicando direção de correção"""
        arrow_length = 30
        arrow_angle = steering_correction * 45  # Converter correção para ângulo

        # Calcular ponta da seta
        import math
        angle_rad = math.radians(arrow_angle)
        end_x = int(x + arrow_length * math.sin(angle_rad))
        end_y = int(y - arrow_length * math.cos(angle_rad))

        # Desenhar seta
        cv2.arrowedLine(self.current_frame, (x, y), (end_x, end_y), color, 3, tipLength=0.3)

    def _draw_dashed_line(self, start, end, color, thickness, dash_length, gap_length):
        """Desenhar linha tracejada"""
        import math
        x1, y1 = start
        x2, y2 = end

        # Calcular distância
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Calcular número de dashes
        total_dash_gap = dash_length + gap_length
        num_dashes = int(distance / total_dash_gap)

        # Desenhar dashes
        for i in range(num_dashes):
            start_dash = i * total_dash_gap
            end_dash = start_dash + dash_length

            if end_dash > distance:
                end_dash = distance

            # Calcular coordenadas
            ratio_start = start_dash / distance
            ratio_end = end_dash / distance

            dash_x1 = int(x1 + (x2 - x1) * ratio_start)
            dash_y1 = int(y1 + (y2 - y1) * ratio_start)
            dash_x2 = int(x1 + (x2 - x1) * ratio_end)
            dash_y2 = int(y1 + (y2 - y1) * ratio_end)

            cv2.line(self.current_frame, (dash_x1, dash_y1), (dash_x2, dash_y2), color, thickness)

    def _draw_info_panel(self, line_info=None):
        """Desenhar painel de informações organizado"""
        height, width = self.current_frame.shape[:2]

        # Fundo semi-transparente para o painel
        panel_width = 320
        panel_height = 240  # Aumentado para acomodar nova linha
        panel_x = width - panel_width - 10
        panel_y = 10

        overlay = self.current_frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y),
                     (panel_x + panel_width, panel_y + panel_height),
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, self.current_frame, 0.2, 0, self.current_frame)

        # Borda do painel
        cv2.rectangle(self.current_frame, (panel_x, panel_y),
                     (panel_x + panel_width, panel_y + panel_height),
                     (255, 255, 255), 2)

        # Título
        cv2.putText(self.current_frame, "AGV - STATUS", (panel_x + 10, panel_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Linha separadora
        cv2.line(self.current_frame, (panel_x + 10, panel_y + 35),
                (panel_x + panel_width - 10, panel_y + 35), (255, 255, 255), 1)

        # Informações organizadas
        info_lines = [
            f"Velocidade: {self.status_info['velocidade']}",
            f"Direcao: {self.status_info['direcao']}",
            f"Erro: {self.status_info['erro_pixels']}px",
            f"Correcao: {self.status_info['correcao']:.3f}",
            f"Linha: {'OK' if self.status_info['linha_detectada'] else 'Nao'}",
            f"QR: {'OK' if self.status_info['qr_detectado'] else 'Nao'}",
            f"Conf.: {self.status_info['confianca']:.2f}",
            f"Sub: {self.status_info['subcorredor'] or 'Nenhum'}"
        ]

        # Adicionar status do quadrado verde se disponível
        if line_info and 'green_square' in line_info:
            gs = line_info['green_square']
            # Determinar se devemos mostrar estado de leitura ou já lido
            recently_read = (time.time() - self.last_qr_time) < 2.0 and self.last_qr_text is not None
            if gs['detected'] and not recently_read:
                status_txt = "VERDE - LENDO EM MOVIMENTO"
                info_lines.append(f"Quadrado: {status_txt}")
            elif gs['detected'] and recently_read:
                info_lines.append("Quadrado: QR LIDO")
            else:
                info_lines.append(f"Quadrado: Nenhum")
        else:
            info_lines.append(f"Quadrado: N/A")

        # Mostrar texto do último QR lido, se houver
        if self.status_info.get('qr_texto'):
            info_lines.append(f"QR Texto: {self.status_info['qr_texto']}")

        for i, line in enumerate(info_lines):
            y_pos = panel_y + 55 + i * 20

            # Cor baseada no conteúdo
            color = (255, 255, 255)  # Branco padrão

            if "OK" in line:
                color = (0, 255, 0)  # Verde para OK
            elif "Nao" in line:
                color = (0, 0, 255)  # Vermelho para Não
            elif "Erro:" in line and abs(self.status_info['erro_pixels']) > 50:
                color = (0, 165, 255)  # Laranja para erro alto

            cv2.putText(self.current_frame, line, (panel_x + 10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def _draw_status_indicators(self):
        """Desenhar indicadores visuais de status"""
        height, width = self.current_frame.shape[:2]

        # 1. Barra de confiança (canto superior esquerdo)
        confidence = self.status_info['confianca']
        bar_width = 150
        bar_height = 20
        bar_x = 10
        bar_y = 10

        # Fundo da barra
        cv2.rectangle(self.current_frame, (bar_x, bar_y),
                     (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)

        # Barra de progresso
        fill_width = int(bar_width * confidence)
        if confidence > 0.8:
            bar_color = (0, 255, 0)  # Verde
        elif confidence > 0.5:
            bar_color = (0, 255, 255)  # Amarelo
        else:
            bar_color = (0, 0, 255)  # Vermelho

        cv2.rectangle(self.current_frame, (bar_x, bar_y),
                     (bar_x + fill_width, bar_y + bar_height), bar_color, -1)

        # Borda e texto
        cv2.rectangle(self.current_frame, (bar_x, bar_y),
                     (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
        cv2.putText(self.current_frame, f"Conf: {confidence:.2f}", (bar_x + 5, bar_y + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 2. Indicador de movimento (canto inferior esquerdo)
        speed = self.status_info['velocidade']
        direction = self.status_info['direcao']

        # Círculo de status
        center_x, center_y = 50, height - 50
        radius = 30

        # Cor baseada na velocidade
        if speed > 0:
            status_color = (0, 255, 0)  # Verde - em movimento
        else:
            status_color = (0, 0, 255)  # Vermelho - parado

        cv2.circle(self.current_frame, (center_x, center_y), radius, status_color, 3)

        # Texto de velocidade
        cv2.putText(self.current_frame, f"{speed}", (center_x - 10, center_y + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # 3. Indicador de direção (seta)
        if "esquerda" in direction:
            self._draw_direction_indicator(center_x, center_y - 60, "←", (0, 165, 255))
        elif "direita" in direction:
            self._draw_direction_indicator(center_x, center_y - 60, "→", (0, 165, 255))
        elif "frente" in direction:
            self._draw_direction_indicator(center_x, center_y - 60, "↑", (0, 255, 0))

    def _draw_direction_indicator(self, x, y, symbol, color):
        """Desenhar indicador de direção com símbolo"""
        cv2.putText(self.current_frame, symbol, (x - 10, y + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

    def _detect_green_square(self, frame):
        """Detectar quadrado verde no frame"""
        try:
            # Converter para HSV para melhor detecção de cor
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Definir range para verde (ajuste conforme necessário - mais permissivo)
            lower_green = np.array([30, 30, 30])   # Verde escuro - mais permissivo
            upper_green = np.array([90, 255, 255]) # Verde claro - mais permissivo

            # Criar máscara para verde
            mask = cv2.inRange(hsv, lower_green, upper_green)

            # Operações morfológicas para limpar a máscara
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Ordenar por área (maior primeiro)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            candidates = []
            for contour in contours:
                # Calcular medidas básicas
                area = cv2.contourArea(contour)
                if area < 800:
                    continue

                x, y, w, h = cv2.boundingRect(contour)
                if w < 40 or h < 40:
                    continue

                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
                vertices = len(approx)
                aspect_ratio = float(w) / h if h > 0 else 999
                extent = area / float(w * h) if (w * h) > 0 else 0.0

                candidates.append({'bbox': (x, y, w, h), 'area': area, 'vertices': vertices,
                                   'aspect': aspect_ratio, 'extent': extent})

                # Critérios mais permissivos
                if 4 <= vertices <= 8 and 0.6 <= aspect_ratio <= 1.6 and extent >= 0.45:
                    return {
                        'detected': True,
                        'bbox': (x, y, w, h),
                        'area': area,
                        'center': (x + w//2, y + h//2),
                        'vertices': vertices,
                        'aspect': aspect_ratio,
                        'extent': extent,
                        'candidates': candidates
                    }

            # Sem detecção forte, retornar candidatos para visualização
            return {'detected': False, 'candidates': candidates}

        except Exception as e:
            print(f"Erro na detecção de quadrado verde: {e}")
            return {'detected': False}

    def _detect_blue_square(self, frame):
        """Detectar marcador (azul ou vermelho) no frame.
        Cor ativa controlada por NAVIGATION_CONFIG['markers']['active'] ("blue" ou "red").
        - Azul: modos legacy (BGR->HSV) ou novo (RGB->HSV + ROI/gates)
        - Vermelho: legacy BGR->HSV com duas faixas (0-10 e 170-180) e portas/gates reaproveitadas
        Retorna dict com detected, bbox, area, center, etc.
        """
        try:
            from config import NAVIGATION_CONFIG as _NC
            markers = _NC.get('markers', {})
            active_color = str(markers.get('active', 'blue')).lower()
            if active_color not in ('blue', 'red'):
                active_color = 'blue'
            cfg = markers.get(active_color, {})
            use_legacy = bool(cfg.get('use_legacy', False))
            h_low = int(cfg.get('h_low', 95))
            h_high = int(cfg.get('h_high', 135))
            s_min = int(cfg.get('s_min', 40))
            v_min = int(cfg.get('v_min', 40))
            roi_start_frac = float(cfg.get('roi_y_start_frac', 0.45))
            min_area = int(cfg.get('min_area', 500))
            min_size_px = int(cfg.get('min_size_px', 30))
            aspect_min = float(cfg.get('aspect_min', 0.6))
            aspect_max = float(cfg.get('aspect_max', 1.6))
            extent_min = float(cfg.get('extent_min', 0.45))
            max_frame_area_frac = float(cfg.get('max_frame_area_frac', 0.2))
            bbox_bottom_min_frac = float(cfg.get('bbox_bottom_min_frac', 0.5))

            H, W = frame.shape[:2]
            if use_legacy and active_color == 'blue':
                # LEGACY: frame é BGR; converter BGR->HSV e usar thresholds clássicos em frame completo
                hsv_full = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower_blue_legacy = np.array([95, 40, 40])
                upper_blue_legacy = np.array([135, 255, 255])
                mask_legacy = cv2.inRange(hsv_full, lower_blue_legacy, upper_blue_legacy)
                kernel = np.ones((5, 5), np.uint8)
                mask_legacy = cv2.morphologyEx(mask_legacy, cv2.MORPH_OPEN, kernel)
                mask_legacy = cv2.morphologyEx(mask_legacy, cv2.MORPH_CLOSE, kernel)
                contours, _ = cv2.findContours(mask_legacy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                for c in contours:
                    area = cv2.contourArea(c)
                    if area < 800:
                        continue
                    x, y, w, h = cv2.boundingRect(c)
                    if w < 40 or h < 40:
                        continue
                    peri = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                    vertices = len(approx)
                    aspect_ratio = float(w) / h if h > 0 else 999
                    extent = area / float(w * h) if (w * h) > 0 else 0.0
                    ok_shape = (4 <= vertices <= 8 and 0.6 <= aspect_ratio <= 1.6 and extent >= 0.45)
                    if not ok_shape:
                        continue
                    # Opcionalmente aplicar gates adicionais mesmo no legado
                    if bool(cfg.get('apply_gates_after_legacy', False)):
                        # Porta por posição vertical/ROI/bordas
                        y0 = y
                        bbox_bottom = y0 + h
                        if bbox_bottom < int(H * float(cfg.get('bbox_bottom_min_frac', 0.5))):
                            continue
                        if y0 < int(H * float(cfg.get('min_y_frac', 0.4))):
                            continue
                        edge_margin_px = int(cfg.get('edge_margin_px', 0))
                        if x < edge_margin_px or (x + w) > (W - edge_margin_px):
                            continue
                        # Porta por centro-x
                        cx = x + w // 2
                        cx_min = int(W * float(cfg.get('center_x_min_frac', 0.0)))
                        cx_max = int(W * float(cfg.get('center_x_max_frac', 1.0)))
                        if not (cx_min <= cx <= cx_max):
                            continue
                        # Porta com linha preta abaixo
                        try:
                            line_gate_min_black_frac = float(cfg.get('line_gate_min_black_frac', 0.0))
                            strip_h_frac = float(cfg.get('line_gate_strip_h_frac', 0.15))
                            if line_gate_min_black_frac > 0.0:
                                strip_y1 = min(H - 1, y + h)
                                strip_y2 = min(H, strip_y1 + max(2, int(h * strip_h_frac)))
                                if strip_y2 > strip_y1:
                                    strip = frame[strip_y1:strip_y2, max(0, x):min(W, x + w)]
                                    strip_hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV)
                                    lower_black = np.array([0, 0, 0])
                                    upper_black = np.array([180, 255, 200])
                                    m_black = cv2.inRange(strip_hsv, lower_black, upper_black)
                                    black_frac = float(np.count_nonzero(m_black)) / float(m_black.size if m_black.size > 0 else 1)
                                    if black_frac < line_gate_min_black_frac:
                                        continue
                        except Exception:
                            pass
                    return {
                        'detected': True,
                        'bbox': (x, y, w, h),
                        'area': area,
                        'center': (x + w//2, y + h//2),
                        'vertices': vertices,
                        'aspect': aspect_ratio,
                        'extent': extent
                    }
                return {'detected': False}

            if use_legacy and active_color == 'red':
                # LEGACY VERMELHO: frame em BGR; duas faixas de H e mesmas portas opcionais
                hsv_full = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                s_min = int(cfg.get('s_min', 70))
                v_min = int(cfg.get('v_min', 60))
                h1_low = int(cfg.get('h1_low', 0))
                h1_high = int(cfg.get('h1_high', 10))
                h2_low = int(cfg.get('h2_low', 170))
                h2_high = int(cfg.get('h2_high', 180))
                lower_red1 = np.array([h1_low, s_min, v_min])
                upper_red1 = np.array([h1_high, 255, 255])
                lower_red2 = np.array([h2_low, s_min, v_min])
                upper_red2 = np.array([h2_high, 255, 255])
                mask1 = cv2.inRange(hsv_full, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv_full, lower_red2, upper_red2)
                mask_legacy = cv2.bitwise_or(mask1, mask2)
                kernel = np.ones((5, 5), np.uint8)
                mask_legacy = cv2.morphologyEx(mask_legacy, cv2.MORPH_OPEN, kernel)
                mask_legacy = cv2.morphologyEx(mask_legacy, cv2.MORPH_CLOSE, kernel)
                contours, _ = cv2.findContours(mask_legacy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                for c in contours:
                    area = cv2.contourArea(c)
                    if area < int(cfg.get('min_area', 800)):
                        continue
                    x, y, w, h = cv2.boundingRect(c)
                    if w < int(cfg.get('min_size_px', 40)) or h < int(cfg.get('min_size_px', 40)):
                        continue
                    peri = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                    vertices = len(approx)
                    aspect_ratio = float(w) / h if h > 0 else 999
                    extent = area / float(w * h) if (w * h) > 0 else 0.0
                    ok_shape = (4 <= vertices <= 8 and float(cfg.get('aspect_min', 0.6)) <= aspect_ratio <= float(cfg.get('aspect_max', 1.6)) and extent >= float(cfg.get('extent_min', 0.45)))
                    if not ok_shape:
                        continue
                    if bool(cfg.get('apply_gates_after_legacy', True)):
                        y0 = y
                        bbox_bottom = y0 + h
                        if bbox_bottom < int(H * float(cfg.get('bbox_bottom_min_frac', 0.55))):
                            continue
                        if y0 < int(H * float(cfg.get('min_y_frac', 0.4))):
                            continue
                        edge_margin_px = int(cfg.get('edge_margin_px', 0))
                        if x < edge_margin_px or (x + w) > (W - edge_margin_px):
                            continue
                        cx = x + w // 2
                        cx_min = int(W * float(cfg.get('center_x_min_frac', 0.2)))
                        cx_max = int(W * float(cfg.get('center_x_max_frac', 0.8)))
                        if not (cx_min <= cx <= cx_max):
                            continue
                        try:
                            line_gate_min_black_frac = float(cfg.get('line_gate_min_black_frac', 0.15))
                            strip_h_frac = float(cfg.get('line_gate_strip_h_frac', 0.20))
                            if line_gate_min_black_frac > 0.0:
                                strip_y1 = min(H - 1, y + h)
                                strip_y2 = min(H, strip_y1 + max(2, int(h * strip_h_frac)))
                                if strip_y2 > strip_y1:
                                    strip = frame[strip_y1:strip_y2, max(0, x):min(W, x + w)]
                                    strip_hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV)
                                    lower_black = np.array([0, 0, 0])
                                    upper_black = np.array([180, 255, 200])
                                    m_black = cv2.inRange(strip_hsv, lower_black, upper_black)
                                    black_frac = float(np.count_nonzero(m_black)) / float(m_black.size if m_black.size > 0 else 1)
                                    if black_frac < line_gate_min_black_frac:
                                        continue
                        except Exception:
                            pass
                    return {
                        'detected': True,
                        'bbox': (x, y, w, h),
                        'area': area,
                        'center': (x + w//2, y + h//2),
                        'vertices': vertices,
                        'aspect': aspect_ratio,
                        'extent': extent
                    }
                return {'detected': False}

            # NOVO (azul): ROI em RGB
            y1 = int(max(0, min(H - 1, H * roi_start_frac)))
            roi = frame[y1:H, :]
            hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
            # Faixa azul em HSV controlada por config
            lower_blue = np.array([h_low, s_min, v_min])
            upper_blue = np.array([h_high, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            # Debug opcional: salvar ROI e máscara lado a lado
            if bool(cfg.get('debug', False)):
                try:
                    roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
                    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                    vis_dbg = np.hstack((roi_bgr, mask_bgr))
                    # Desenhar até 3 maiores contornos
                    for i, c_dbg in enumerate(contours[:3]):
                        x_d, y_d, w_d, h_d = cv2.boundingRect(c_dbg)
                        cv2.rectangle(vis_dbg, (x_d, y_d), (x_d + w_d, y_d + h_d), (255, 0, 0), 2)
                    cv2.putText(vis_dbg, f"HSV H:[{h_low},{h_high}] S>={s_min} V>={v_min}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
                    os.makedirs(getattr(self, 'snapshots_dir', './snapshots'), exist_ok=True)
                    cv2.imwrite(os.path.join(self.snapshots_dir, f'blue_debug_{int(time.time()*1000)}.png'), vis_dbg)
                except Exception:
                    pass
            for c in contours:
                area = cv2.contourArea(c)
                if area < min_area:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                if w < min_size_px or h < min_size_px:
                    continue
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                vertices = len(approx)
                aspect_ratio = float(w) / h if h > 0 else 999
                extent = area / float(w * h) if (w * h) > 0 else 0.0
                # Coordenadas no frame original (ajustar y com o offset do ROI)
                x0, y0 = x, y + y1
                # Ignorar objetos gigantes (provavelmente estante/parede)
                if (area / float((W * H) if W * H > 0 else 1)) > max_frame_area_frac:
                    continue
                # Exigir que a base do bbox esteja na metade inferior do frame (evita objetos altos)
                bbox_bottom = y0 + h
                if bbox_bottom < int(H * bbox_bottom_min_frac):
                    continue
                # Exigir que o topo do bbox não esteja muito alto
                min_y_frac = float(cfg.get('min_y_frac', 0.4))
                if y0 < int(H * min_y_frac):
                    continue
                # Ignorar detecções coladas nas bordas
                edge_margin_px = int(cfg.get('edge_margin_px', 0))
                if x0 < edge_margin_px or (x0 + w) > (W - edge_margin_px):
                    continue
                if 4 <= vertices <= 8 and aspect_min <= aspect_ratio <= aspect_max and extent >= extent_min:
                    # Porta com a linha preta abaixo: checar um strip logo abaixo do bbox
                    try:
                        line_gate_min_black_frac = float(cfg.get('line_gate_min_black_frac', 0.0))
                        strip_h_frac = float(cfg.get('line_gate_strip_h_frac', 0.15))
                        if line_gate_min_black_frac > 0.0:
                            strip_y1 = min(H - 1, y0 + h)
                            strip_y2 = min(H, strip_y1 + max(2, int(h * strip_h_frac)))
                            if strip_y2 > strip_y1:
                                strip = frame[strip_y1:strip_y2, max(0, x0):min(W, x0 + w)]
                                # Usar detecção de preto do LineDetector (aproximação via HSV)
                                strip_bgr = cv2.cvtColor(strip, cv2.COLOR_RGB2BGR)
                                strip_hsv = cv2.cvtColor(strip_bgr, cv2.COLOR_BGR2HSV)
                                lower_black = np.array([0, 0, 0])
                                upper_black = np.array([180, 255, 200])
                                m_black = cv2.inRange(strip_hsv, lower_black, upper_black)
                                black_frac = float(np.count_nonzero(m_black)) / float(m_black.size if m_black.size > 0 else 1)
                                if black_frac < line_gate_min_black_frac:
                                    # Sem linha preta imediatamente abaixo, ignorar
                                    continue
                    except Exception:
                        pass
                    # Porta por posição horizontal: forçar centro-x do bbox numa janela central
                    cx = x0 + w // 2
                    cx_min = int(W * float(cfg.get('center_x_min_frac', 0.0)))
                    cx_max = int(W * float(cfg.get('center_x_max_frac', 1.0)))
                    if not (cx_min <= cx <= cx_max):
                        continue
                    return {
                        'detected': True,
                        'bbox': (x0, y0, w, h),
                        'area': area,
                        'center': (x0 + w//2, y0 + h//2),
                        'vertices': vertices,
                        'aspect': aspect_ratio,
                        'extent': extent
                    }
            return {'detected': False}
        except Exception as e:
            print(f"Erro na detecção de quadrado azul: {e}")
            return {'detected': False}

    def go_until_blue_then_turn_right_until_green(self, drive_speed=20, turn_speed_fast=22, turn_speed_slow=8,
                                                 timeout_drive=20.0, timeout_turn=12.0,
                                                 min_turn_time_s=0.8, green_persist_frames=3, green_min_area=1400,
                                                 turn_direction='direita', invert_turn=False,
                                                 follow_line_while_search=True,
                                                 ignore_right_black_during_blue=False,
                                                 ignore_right_frac=0.35,
                                                align_after_turn=True,
                                                 align_timeout_s=3.0,
                                                 align_tol_px=22,
                                                 align_min_conf=0.45,
                                                 align_pulse_speed=12,
                                                 align_pulse_s=0.06,
                                                 scan_shelf_qr_after_turn=False,
                                                 shelf_cam_index=0,
                                                 shelf_scan_time_s=3.0,
                                                 shelf_scan_debug=False,
                                                 shelf_debug_dir=None,
                                                 shelf_debug_prefix='shelf_qr',
                                                 shelf_expected_qr=None,
                                                post_match_forward_s=2.0,
                                                post_match_forward_speed=25,
                                                require_centered_green=True,
                                                green_center_tol_px=40):
        """Fluxo: seguir linha e avançar até AZUL; foto; girar (visão) até VERDE; alinhar à linha preta.
        - follow_line_while_search: aplica micro-correções na busca do azul
        - align_after_turn: faz alinhamento do centro da linha após parar no verde
        """
        print("🧭 Rotina: frente até AZUL, foto, curva à direita até VERDE (sem giroscópio)")
        # Garantir câmera ativa
        if not self.line_detector.picam2:
            if not self.line_detector.initialize():
                print("❌ Falha ao iniciar câmera para a rotina azul->verde")
                return False
        # Iniciar captura contínua para estabilidade
        started_cont = False
        try:
            started_cont = self.line_detector.start_continuous_capture()
        except Exception as e:
            print(f"⚠️ Falha ao iniciar captura contínua: {e}")

        # Helper: mapear comando de giro conforme inversão global
        def map_turn(cmd_name: str) -> str:
            try:
                from config import NAVIGATION_CONFIG as _NC, HARDWARE_CONFIG as _HC
                inv = bool(_NC.get('turn', {}).get('invert_commands', False)) or bool(_HC.get('motors', {}).get('invert_turn_commands', False))
            except Exception:
                inv = False
            if not inv:
                return cmd_name
            if cmd_name == 'virar_direita':
                return 'virar_esquerda'
            if cmd_name == 'virar_esquerda':
                return 'virar_direita'
            return cmd_name

        # 1) Andar para frente até detectar azul (seguindo a linha com micro-correções)
        t0 = time.time()
        if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
            self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': drive_speed})
        blue_found = None
        in_pulse = False
        pulse_until = 0.0
        last_forward_keepalive = 0.0
        forward_keepalive_interval = 0.6
        while time.time() - t0 < timeout_drive:
            frame = self.line_detector.capture_continuous_frame() if started_cont else self.line_detector.capture_frame()
            if frame is None:
                time.sleep(0.05)
                continue
            # Escolher formato do frame conforme o modo (legacy usa BGR; novo usa RGB)
            try:
                from config import NAVIGATION_CONFIG as _NC
                _markers = _NC.get('markers', {})
                _active = str(_markers.get('active', 'blue')).lower()
                _cfg = _markers.get(_active, {})
                _use_legacy = bool(_cfg.get('use_legacy', False))
            except Exception:
                _active = 'blue'
                _use_legacy = False
            frame_for_detect = None
            vis_base_bgr = None
            if _use_legacy or _active == 'red':
                # Converter para BGR e detectar no modo legado
                frame_for_detect = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                vis_base_bgr = frame_for_detect.copy()
            else:
                # Modo novo usa RGB diretamente; manter BGR apenas para salvar
                frame_for_detect = frame
                vis_base_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            blue = self._detect_blue_square(frame_for_detect)
            if blue.get('detected'):
                print("🔵 Quadrado azul detectado — tirando foto e parando")
                try:
                    os.makedirs(self.snapshots_dir, exist_ok=True)
                    # Desenhar anotação do quadrado azul encontrado antes de salvar
                    vis = vis_base_bgr.copy()
                    bx, by, bw, bh = blue.get('bbox', (0, 0, 0, 0))
                    if bw > 0 and bh > 0:
                        cv2.rectangle(vis, (bx, by), (bx + bw, by + bh), (255, 0, 0), 2)
                        cv2.putText(vis, 'BLUE FOUND', (bx, max(30, by - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                        try:
                            cx, cy = blue.get('center', (bx + bw // 2, by + bh // 2))
                            cv2.circle(vis, (int(cx), int(cy)), 5, (255, 0, 0), -1)
                        except Exception:
                            pass
                    cv2.imwrite(os.path.join(self.snapshots_dir, f'blue_found_{int(time.time()*1000)}.png'), vis)
                except Exception:
                    pass
                self.basic_nav.parar()
                blue_found = blue
                break
            # Seguir a mesma lógica padrão do controle da linha preta enquanto busca o azul
            if follow_line_while_search:
                # Opcional: ignorar a parte direita do preto (mascarar área direita do frame em branco)
                frame_for_line = frame
                try:
                    if ignore_right_black_during_blue:
                        H, W = frame.shape[:2]
                        cut_x = int(max(0, min(W, W * (1.0 - float(ignore_right_frac)))))
                        if cut_x < W:
                            frame_for_line = frame.copy()
                            frame_for_line[:, cut_x:W, :] = 255  # branco para não contar como preto
                except Exception:
                    frame_for_line = frame

                info = self.line_detector.process_frame(frame_for_line)
                esp32_available = hasattr(self.basic_nav, 'mpu') and getattr(self.basic_nav.mpu, 'serial_conn', None) is not None
                if info and info.get('detected'):
                    steering_raw = info.get('steering_correction', 0.0)
                    steering_correction = max(-1.0, min(1.0, float(steering_raw) * self.steering_gain))
                    base_speed = int(drive_speed)
                    if abs(steering_correction) < 0.03:
                        # Movimento reto
                        if esp32_available:
                            self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                    elif abs(steering_correction) < 0.2:
                        # Correção leve com redução
                        reduced_speed = max(self.speed_min, base_speed - int(abs(steering_correction) * 14))
                        if esp32_available:
                            self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': reduced_speed})
                    else:
                        # Pulso de correção, mesma convenção: >0 vira esquerda, <0 vira direita
                        correction_speed = max(10, min(22, int(abs(steering_correction) * 18)))
                        if esp32_available:
                            if steering_correction > 0:
                                self.basic_nav.mpu.enviar_comando('virar_esquerda', {'velocidade': correction_speed})
                            else:
                                self.basic_nav.mpu.enviar_comando('virar_direita', {'velocidade': correction_speed})
                            time.sleep(0.03)
                            self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                else:
                    # Linha não detectada momentaneamente: avance devagar e continue procurando
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': max(12, int(drive_speed * 0.6))})
                        time.sleep(0.10)
            time.sleep(0.05)
        if not blue_found:
            print("⏱️ Timeout: azul não encontrado")
            try:
                if started_cont:
                    self.line_detector.stop_continuous_capture()
            except Exception:
                pass
            return False

        # 2) Curvar à direita por visão até encontrar quadrado verde (sem giroscópio)
        print("🔄 Iniciando curva à direita guiada por visão até encontrar VERDE")
        t1 = time.time()
        last_speed = None
        last_cmd_time = 0.0
        cmd_interval = 0.25
        green_streak = 0
        # Mapear comando de giro conforme direção desejada e possível inversão
        try:
            inv_cfg = False
            try:
                from config import NAVIGATION_CONFIG, HARDWARE_CONFIG
                inv_cfg = bool(NAVIGATION_CONFIG.get('turn', {}).get('invert_commands', False)) or bool(HARDWARE_CONFIG.get('motors', {}).get('invert_turn_commands', False))
            except Exception:
                inv_cfg = False
            invert = bool(invert_turn or inv_cfg)
        except Exception:
            invert = bool(invert_turn)
        cmd_turn = 'virar_direita' if str(turn_direction).lower() == 'direita' else 'virar_esquerda'
        if invert:
            cmd_turn = 'virar_esquerda' if cmd_turn == 'virar_direita' else 'virar_direita'
        print(f"↪️ Direção física desejada: {turn_direction} | comando enviado: {cmd_turn}{' (invertido)' if invert else ''}")
        if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
            self.basic_nav.mpu.enviar_comando(cmd_turn, {'velocidade': turn_speed_fast})
            last_speed = turn_speed_fast
        while time.time() - t1 < timeout_turn:
            frame = self.line_detector.capture_continuous_frame() if started_cont else self.line_detector.capture_frame()
            if frame is None:
                time.sleep(0.05)
                continue
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            elapsed_turn = time.time() - t1
            green = {'detected': False}
            try:
                y1 = self.line_detector.roi_y_start
                y2 = y1 + self.line_detector.roi_height
                roi_bgr = frame_bgr[y1:y2, :]
                green_roi = self._detect_green_square(roi_bgr)
                if green_roi.get('detected') and green_roi.get('area', 0) >= green_min_area:
                    green = green_roi
            except Exception:
                pass
            if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None) and last_speed is not None:
                if time.time() - last_cmd_time >= cmd_interval:
                    self.basic_nav.mpu.enviar_comando(cmd_turn, {'velocidade': int(last_speed)})
                    last_cmd_time = time.time()
            info = self.line_detector.process_frame(frame)
            if info and info.get('detected'):
                img_center = self.line_detector.width // 2
                err_raw = int(info.get('center', img_center)) - img_center
                abs_err = abs(err_raw)
                speed_cmd = turn_speed_slow if abs_err < 100 else turn_speed_fast
                if speed_cmd != last_speed and getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                    self.basic_nav.mpu.enviar_comando(cmd_turn, {'velocidade': speed_cmd})
                    last_speed = speed_cmd
            if elapsed_turn >= min_turn_time_s and green.get('detected'):
                green_streak += 1
            else:
                green_streak = 0
            if green_streak >= green_persist_frames:
                print("🟩 Quadrado verde encontrado (persistente) — parando curva")
                self.basic_nav.parar()
                try:
                    os.makedirs(self.snapshots_dir, exist_ok=True)
                    y1 = self.line_detector.roi_y_start
                    bx, by, bw, bh = green.get('bbox', (0,0,0,0))
                    vis = frame_bgr.copy()
                    cv2.rectangle(vis, (bx, y1 + by), (bx + bw, y1 + by + bh), (0, 255, 0), 2)
                    cv2.putText(vis, 'GREEN FOUND', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    cv2.imwrite(os.path.join(self.snapshots_dir, f'green_found_{int(time.time()*1000)}.png'), vis)
                except Exception:
                    pass
                # 3) Opcional: alinhar ao centro da linha preta após a curva
                if align_after_turn:
                    print("🧭 Alinhando ao centro da linha preta após a curva...")
                    align_start = time.time()
                    aligned = False
                    while time.time() - align_start < align_timeout_s:
                        frame2 = self.line_detector.capture_continuous_frame() if started_cont else self.line_detector.capture_frame()
                        if frame2 is None:
                            time.sleep(0.03)
                            continue
                        info2 = self.line_detector.process_frame(frame2)
                        if info2 and info2.get('detected') and info2.get('confidence', 0) >= align_min_conf:
                            img_center2 = self.line_detector.width // 2
                            err_px2 = int(info2.get('center', img_center2)) - img_center2
                            if abs(err_px2) <= align_tol_px:
                                print(f"✅ Linha alinhada (erro {err_px2}px)")
                                aligned = True
                                break
                            nominal2 = 'virar_direita' if err_px2 > 0 else 'virar_esquerda'
                            turn_cmd2 = map_turn(nominal2)
                            try:
                                if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                                    self.basic_nav.mpu.enviar_comando(turn_cmd2, {'velocidade': int(align_pulse_speed)})
                                time.sleep(max(0.04, float(align_pulse_s)))
                                self.basic_nav.parar()
                            except Exception:
                                pass
                            time.sleep(0.04)
                        else:
                            try:
                                if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                                    self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': max(12, int(drive_speed * 0.6))})
                                time.sleep(0.12)
                                self.basic_nav.parar()
                            except Exception:
                                pass
                    if not aligned:
                        print("⚠️ Alinhamento por visão não atingiu tolerância no tempo limite, seguindo assim mesmo")
                # 4) Opcional: após curva, ligar outra câmera e ler QR na estante
                if scan_shelf_qr_after_turn:
                    print("📷 Lendo QR codes da estante com a outra câmera...")
                    try:
                        # Parar captura contínua antes de abrir outra câmera (evita conflito de device)
                        try:
                            if started_cont:
                                self.line_detector.stop_continuous_capture()
                                started_cont = False
                        except Exception:
                            pass
                        # Honrar o índice solicitado (p.ex., 0 em alta resolução). Como paramos a captura contínua,
                        # é seguro reutilizar a mesma câmera do seguidor de linha.
                        selected_idx = int(shelf_cam_index)
                        results = self._scan_shelf_qr_secondary_camera(
                            camera_index=int(selected_idx),
                            duration_s=float(shelf_scan_time_s),
                            debug=bool(shelf_scan_debug),
                            debug_dir=shelf_debug_dir,
                            debug_prefix=shelf_debug_prefix,
                        )
                        if results:
                            textos = [r.get('data', '') for r in results if r.get('data')]
                            unicos = []
                            for t in textos:
                                if t not in unicos:
                                    unicos.append(t)
                            print(f"🧾 QR codes presentes na estante ({len(unicos)}):")
                            for t in unicos:
                                print(f"   • {t}")
                            # Se houver um QR esperado, e foi encontrado, avançar reto por X segundos
                            try:
                                if shelf_expected_qr:
                                    matched = any(t == shelf_expected_qr for t in unicos)
                                    if not matched:
                                        # fallback: contains match (caso venha com sufixos/variantes)
                                        matched = any(shelf_expected_qr in t for t in unicos)
                                    if matched:
                                        fwd_speed = int(post_match_forward_speed) if post_match_forward_speed is not None else int(drive_speed)
                                        dur = max(0.0, float(post_match_forward_s))
                                        if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None) and dur > 0:
                                            print(f"➡️ QR esperado encontrado: '{shelf_expected_qr}'. Avançando reto por {dur:.2f}s...")
                                            self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': fwd_speed})
                                            time.sleep(dur)
                                            self.basic_nav.parar()
                            except Exception as e:
                                print(f"⚠️ Falha ao executar avanço pós-leitura: {e}")
                        else:
                            print("⚠️ Nenhum QR code detectado na estante no período de varredura")

                        # Informar caminho da imagem anotada, independentemente de ter encontrado QR
                        try:
                            img_path = getattr(self, 'last_shelf_qr_image_path', None)
                            if img_path:
                                print(f"🖼️ Foto com marcações dos QR salva em: {img_path}")
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"⚠️ Falha ao escanear QR na estante: {e}")
                try:
                    if started_cont:
                        self.line_detector.stop_continuous_capture()
                except Exception:
                    pass
                return True
            time.sleep(0.05)

        print("⏱️ Timeout: verde não encontrado durante a curva")
        self.basic_nav.parar()
        try:
            if started_cont:
                self.line_detector.stop_continuous_capture()
        except Exception:
            pass
        return False

    def initialize(self):
        """Inicializar todos os componentes"""
        print("INICIALIZANDO NAVEGAÇÃO SEGUINDO LINHA")
        print("=" * 45)

        success = True
        system = platform.system().lower()

        # Inicializar navegação básica (pode falhar no Windows sem ESP32)
        if not self.basic_nav.inicializar():
            if system == 'windows':
                print("⚠️ ESP32 não disponível no Windows - modo simulação ativado")
                print("✅ Navegação básica em modo simulação")
            else:
                print("Falha na navegacao basica")
                success = False

        # Inicializar detector de linha
        if not self.line_detector.initialize():
            print("❌ Falha no detector de linha")
            success = False
        else:
            # Entregar detector compartilhado para a navegação básica
            try:
                if hasattr(self.basic_nav, 'set_shared_detector'):
                    self.basic_nav.set_shared_detector(self.line_detector)
            except Exception:
                pass

        # Inicializar detector QR (opcional - usa pyzbar diretamente)
        try:
            import pyzbar
            print("✅ pyzbar disponível para leitura de QR codes")
        except ImportError:
            print("⚠️ pyzbar não disponível - leitura de QR codes desabilitada")

        if success:
            print("✅ Navegação seguindo linha inicializada!")
            if system == 'windows':
                print("💡 Modo Windows: Use para testes visuais e simulação")
        else:
            print("❌ Falha na inicialização")

        return success

    def calculate_motor_speeds(self, steering_correction):
        """Calcular velocidades dos motores baseado na correção de direção (LEGACY - não usado)"""
        # Este método não é mais usado pois o controle é feito via comandos do ESP32
        correction = steering_correction * self.steering_sensitivity
        left_speed = self.speed_base - (correction * (self.speed_base - self.speed_min))
        right_speed = self.speed_base + (correction * (self.speed_base - self.speed_min))
        left_speed = max(self.speed_min, min(self.speed_max, left_speed))
        right_speed = max(self.speed_min, min(self.speed_max, right_speed))
        return int(left_speed), int(right_speed)

    def follow_line_step(self):
        """Executar um passo de seguimento de linha com detecção de QR codes"""
        try:
            # Detectar linha
            line_info = self.line_detector.process_frame()

            if not line_info or not line_info['detected']:
                print("⚠️ Linha não detectada - parando")
                self.status_info.update({
                    'velocidade': 0,
                    'direcao': 'parado',
                    'linha_detectada': False,
                    'qr_detectado': False
                })
                # Mostrar ROI mesmo sem detecção para visualizar câmera
                roi = line_info.get('roi') if line_info else None
                self.update_visual_frame(roi, line_info)

                # Só parar motores se ESP32 estiver disponível
                if hasattr(self.basic_nav, 'mpu') and self.basic_nav.mpu.serial_conn:
                    self.basic_nav.parar()
                return False

            # Obter frame atual para possível detecção QR
            # Usar ROI do detector de linha por padrão; manter frame completo disponível se necessário
            current_frame = line_info.get('roi')
            full_frame = line_info.get('frame_bgr')

            # Primeiro, verificar se há quadrado verde (prioridade alta)
            green_square = self._detect_green_square(current_frame) if current_frame is not None else {'detected': False}

            # Obter correção de direção calculada pelo detector e aplicar ganho adicional
            steering_raw = line_info['steering_correction']
            steering_correction = max(-1.0, min(1.0, steering_raw * self.steering_gain))
            error_pixels = line_info['center'] - (self.line_detector.width // 2)

            print(f"📏 Centro linha: {line_info['center']}, Erro: {error_pixels}px, Correção: {steering_correction:.3f} (raw={steering_raw:.3f}, gain={self.steering_gain})")

            # QR code SÓ é lido quando quadrado verde é detectado
            qr_content = None
            qr_source = None  # 'green_square' ou 'line_detection'
            # Verificar disponibilidade do ESP32 apenas uma vez
            esp32_available = hasattr(self.basic_nav, 'mpu') and getattr(self.basic_nav.mpu, 'serial_conn', None) is not None
            if not esp32_available and not getattr(self, '_warned_no_esp32', False):
                print("⚠️ ESP32 não conectado (sem comandos de movimento). Visual e detecção funcionando, mas sem locomoção.")
                print("   Verifique a porta no config.py (esp32.port) e o cabo USB. Use o teste em navigation_basic.py.")
                self._warned_no_esp32 = True

            if green_square['detected']:
                # Quadrado verde detectado - PARAR e focar nessa área para QR (evitar blur)
                print("🟢 Quadrado verde detectado - PARANDO e lendo QR")

                # Parar e estabilizar brevemente
                if esp32_available and (time.time() - self.last_green_stop_time) > 0.8:
                    self.basic_nav.parar()
                    time.sleep(0.25)
                    self.last_green_stop_time = time.time()

                # Re-capturar frame estabilizado
                refreshed = self.line_detector.process_frame()
                if refreshed and refreshed.get('roi') is not None:
                    current_frame = refreshed.get('roi')
                    line_info.update({
                        'roi': current_frame,
                        'detected': refreshed.get('detected', line_info.get('detected')),
                        'center': refreshed.get('center', line_info.get('center')),
                        'confidence': refreshed.get('confidence', line_info.get('confidence'))
                    })
                # Recalcular quadrado verde no frame estabilizado
                green_square = self._detect_green_square(current_frame) if current_frame is not None else {'detected': False}
                if green_square.get('detected'):
                    x, y, w, h = green_square['bbox']

                    # Expandir de forma assimétrica: mais margem acima (direção de avanço) para capturar o QR mais cedo
                    margin_left = 120
                    margin_right = 120
                    margin_top = 220   # olhar mais à frente
                    margin_bottom = 80 # menos abaixo

                    x_start = max(0, x - margin_left)
                    y_start = max(0, y - margin_top)
                    x_end = min(current_frame.shape[1], x + w + margin_right)
                    y_end = min(current_frame.shape[0], y + h + margin_bottom)

                    roi_qr = current_frame[y_start:y_end, x_start:x_end]
                else:
                    # Fallback: usar frame atual inteiro como ROI se perder o verde após estabilizar
                    roi_qr = current_frame

                try:
                    decoded = self._decode_qr_multi(roi_qr)

                    if decoded:
                        # Popular overlays com offset da ROI expandida
                        # Popular overlays com offset da ROI expandida
                        qrs_overlay = []
                        for d in decoded:
                            bx, by, bw, bh = d.get('bbox', (0, 0, 0, 0))
                            qrs_overlay.append({'bbox': (x_start + bx, y_start + by, bw, bh),
                                                'data': d.get('data', '')})
                        line_info['qr_codes'] = qrs_overlay

                        qr_content = decoded[0].get('data', '')
                        qr_source = 'green_square'
                        if qr_content:
                            # Detectar se é um QR novo (para evitar ações repetidas)
                            is_new_qr = (qr_content != self.last_qr_text)
                            # Imprimir apenas se for diferente do último ou passou tempo suficiente
                            if is_new_qr or (time.time() - self.last_qr_time) > 1.0:
                                print(f"🟢 QR lido: {qr_content}")
                            # Atualizar estado de última leitura
                            self.last_qr_text = qr_content
                            self.last_qr_time = time.time()

                            # Salvar snapshot de sucesso
                            try:
                                self._save_snapshot(current_frame, line_info, 'qr_ok')
                            except Exception:
                                pass

                            # Verificar se é um QR code de subcorredor
                            if qr_content.startswith('Corredor') and '_' in qr_content:
                                self.current_subcorredor = qr_content
                                print(f"🏢 Subcorredor detectado via quadrado verde: {qr_content}")

                            # Após ler QUALQUER QR code, avançar reto por alguns segundos para não interferir no seguimento da linha
                            try:
                                post_cfg = NAVIGATION_CONFIG.get('qr_post_read', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
                                forward_sec = float(post_cfg.get('forward_seconds', 2.0))
                                forward_speed = int(post_cfg.get('forward_speed', self.speed_base))
                                if esp32_available and is_new_qr and forward_sec > 0:
                                    print(f"🚗 QR lido — avançando reto por {forward_sec:.1f}s (velocidade={forward_speed})")
                                    self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': forward_speed})
                                    time.sleep(forward_sec)
                                    # Não para explicitamente aqui; próxima iteração do loop retomará o controle fino
                                    # Evitar outros comandos nesta iteração
                                    return True
                            except Exception as e:
                                print(f"⚠️ Falha ao avançar após QR: {e}")
                except Exception as e:
                    print(f"Erro ao ler QR no quadrado verde: {e}")
                finally:
                    # Snapshot de falha (somente se não leu agora e respeitando cooldown)
                    if not qr_content:
                        now_ts = time.time()
                        if (now_ts - self.last_snapshot_time) > self.snapshot_cooldown:
                            try:
                                if 'qr_codes' not in line_info:
                                    line_info['qr_codes'] = []
                                self._save_snapshot(current_frame, line_info, 'qr_fail')
                            except Exception:
                                pass
                            self.last_snapshot_time = now_ts

            # NÃO há mais leitura de QR em outras condições - apenas quando há quadrado verde

            # Atualizar status
            direcao = 'frente'
            velocidade = self.speed_base

            # Só enviar comandos se ESP32 estiver disponível (já calculado)

            # Determinar se devemos desacelerar (apenas enquanto ainda não leu ou não está em cooldown)
            recently_read = (time.time() - self.last_qr_time) < 2.0 and self.last_qr_text is not None
            slow_mode_active = green_square['detected'] and not (recently_read or qr_content is not None)

            if slow_mode_active:
                # Quadrado verde detectado e ainda não lemos QR agora/recentemente
                direcao = 'verde_lendo_movimento'
                velocidade = 12
                if esp32_available:
                    self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': velocidade})
                # Marcar recente apenas se QR foi realmente detectado
                self.qr_detected_recently = bool(qr_content)

                # Iniciar e gerenciar temporização de micro-parada
                now = time.time()
                if self.green_since_time is None:
                    self.green_since_time = now
                # Se já estamos vendo verde por >1.0s sem leitura recente, dar micro-parada
                if (now - self.green_since_time) > 1.0 and not recently_read and (now - self.last_green_stop_time) > 2.0:
                    if esp32_available:
                        print("⏸️ Micro-parada para estabilizar leitura do QR")
                        self.basic_nav.parar()
                        time.sleep(0.3)
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': velocidade})
                    self.last_green_stop_time = now
            else:
                # Movimento normal - sem detecção de QR
                self.qr_detected_recently = False
                # Resetar temporização do verde
                self.green_since_time = None

                # Correção gradual: pequenas correções intercaladas com movimento para frente
                base_speed = self.speed_base

                if abs(steering_correction) < 0.03:
                    # Movimento reto normal - manter por mais tempo
                    print("➡️ Movimento reto")
                    direcao = 'frente'
                    velocidade = base_speed
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                elif abs(steering_correction) < 0.2:
                    # Correção leve - movimento para frente com velocidade reduzida
                    reduced_speed = max(self.speed_min, base_speed - int(abs(steering_correction) * 14))
                    print(f"🔄 Correção leve ({steering_correction:.3f}) - velocidade reduzida: {reduced_speed}")
                    direcao = 'frente_corrigido'
                    velocidade = reduced_speed
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': reduced_speed})
                else:
                    # Correção necessária - impulso de correção mais rápido
                    # INVERTER A DIREÇÃO: steering_correction > 0 significa linha à direita, então virar para ESQUERDA
                    correction_speed = max(10, min(22, int(abs(steering_correction) * 18)))  # mais agressivo

                    if steering_correction > 0:
                        # Linha à direita - virar para ESQUERDA (invertido)
                        print(f"↪️ Correção esquerda rápida (impulso: {correction_speed})")
                        direcao = 'corrigindo_esquerda'
                        velocidade = correction_speed
                        if esp32_available:
                            self.basic_nav.mpu.enviar_comando('virar_esquerda', {'velocidade': correction_speed})
                    else:
                        # Linha à esquerda - virar para DIREITA (invertido)
                        print(f"↩️ Correção direita rápida (impulso: {correction_speed})")
                        direcao = 'corrigindo_direita'
                        velocidade = correction_speed
                        if esp32_available:
                            self.basic_nav.mpu.enviar_comando('virar_direita', {'velocidade': correction_speed})

                    # Imediatamente voltar ao movimento para frente (pausa menor)
                    if esp32_available:
                        time.sleep(0.03)  # impulso um pouco mais longo para efetivar correção
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                    direcao = 'frente_apos_correcao'
                    velocidade = base_speed

            # Atualizar informações de status
            self.status_info.update({
                'velocidade': velocidade,
                'direcao': direcao,
                'erro_pixels': error_pixels,
                'correcao': steering_correction,
                'qr_detectado': bool(qr_content),  # True somente quando QR foi lido
                'linha_detectada': True,
                'confianca': line_info.get('confidence', 0.0),
                'subcorredor': self.current_subcorredor,
                'qr_texto': self.last_qr_text if (time.time() - self.last_qr_time) < 5.0 else None
            })

            # Adicionar info do quadrado verde ao line_info para visualização
            line_info['green_square'] = green_square

            # Atualizar display visual
            self.update_visual_frame(line_info.get('roi'), line_info)

            return True

        except Exception as e:
            print(f"❌ Erro no seguimento de linha: {e}")
            self.status_info.update({
                'velocidade': 0,
                'direcao': 'erro',
                'linha_detectada': False
            })
            self.update_visual_frame(None)
            self.basic_nav.parar()
            return False

    def detect_intersection(self):
        """Detectar interseção na linha (formato T)"""
        try:
            # Verificar se há expansão da linha (interseção)
            line_info = self.line_detector.process_frame()

            if line_info and line_info['detected']:
                # Se a linha ficou muito larga, pode ser interseção
                if line_info['width'] > self.line_detector.max_line_width * 1.5:
                    if not self.intersection_detected:
                        self.intersection_detected = True
                        print("🔀 Interseção detectada!")
                        return True
                else:
                    self.intersection_detected = False

            return self.intersection_detected

        except Exception as e:
            print(f"Erro na detecção de interseção: {e}")
            return False

    def check_qr_codes(self):
        """Verificar QR codes durante a navegação - usa pyzbar diretamente"""
        try:
            # Obter frame atual do detector de linha
            line_info = self.line_detector.process_frame()
            if not line_info or line_info.get('roi') is None:
                return None

            current_frame = line_info['roi']

            # Detectar QR codes usando pyzbar
            from pyzbar.pyzbar import decode
            qr_codes = decode(current_frame)

            if qr_codes:
                qr_code = qr_codes[0].data.decode('utf-8')
                print(f"📷 QR code detectado durante navegação: {qr_code}")

                # Verificar se é um QR code de subcorredor
                if qr_code.startswith('Corredor') and '_' in qr_code:
                    return qr_code

            return None

        except ImportError:
            print("⚠️ pyzbar não disponível")
            return None
        except Exception as e:
            print(f"Erro na verificação de QR codes: {e}")
            return None

    def navigate_to_intersection(self, target_subcorredor):
        """Navegar até encontrar a interseção do subcorredor alvo"""
        print(f"🎯 Navegando até interseção do subcorredor: {target_subcorredor}")

    # Preparar padrões aceitos para o QR, aceitando dígitos com e sem zero à esquerda
        expected_labels = set()
        code = (target_subcorredor or "").strip()
        expected_labels.add(f"Corredor{code}")  # ex.: Corredor1_1 ou Corredor01_01
        if '_' in code:
            try:
                cc_raw, ss_raw = code.split('_', 1)
                cc_i = int(cc_raw)
                ss_i = int(ss_raw)
                cc_1 = str(cc_i)          # "1"
                ss_1 = str(ss_i)          # "1"
                cc_2 = f"{cc_i:02d}"      # "01"
                ss_2 = f"{ss_i:02d}"      # "01"

                # Formatos possíveis dos QRs impressos
                expected_labels.update({
                    f"Corredor{cc_1}_SubCorredor{ss_1}",
                    f"Corredor{cc_2}_SubCorredor{ss_2}",
                    f"Corredor{cc_1}_{ss_1}",
                    f"Corredor{cc_2}_{ss_2}",
                })
            except Exception:
                pass

        print(f"🔎 Aceitando formatos de QR: {', '.join(sorted(expected_labels))}")

        start_time = time.time()
        qr_found = None

        while not self.stop_event.is_set():
            # Seguir linha
            if not self.follow_line_step():
                break

            # Se o QR do subcorredor já foi detectado no bloco do quadrado verde, aceitar e prosseguir
            if self.current_subcorredor:
                qr_norm = self.current_subcorredor.strip()
                if qr_norm in expected_labels:
                    print(f"✅ Subcorredor reconhecido via QR (verde): {qr_norm}")
                    qr_found = qr_norm
                    break

            # Verificar interseção
            if self.detect_intersection():
                print("🔀 Interseção encontrada!")

                # Verificar QR code na interseção
                qr_found = self.check_qr_codes()

                # Normalizar detecção: remover espaços extras
                qr_norm = qr_found.strip() if qr_found else None

                if qr_norm and (qr_norm in expected_labels):
                    print(f"✅ Subcorredor correto encontrado: {qr_norm}")
                    break
                else:
                    exp_all = sorted(expected_labels)
                    print(f"⚠️ Subcorredor errado ou QR não encontrado: {qr_found} (esperado: {', '.join(exp_all)})")
                    # Continuar procurando

            # Timeout
            if time.time() - start_time > 30:  # 30 segundos máximo
                print("⏰ Timeout na navegação até interseção")
                break

            time.sleep(0.1)

        return qr_found

    def enter_subcorredor(self):
        """Entrar no subcorredor após encontrar a interseção"""
        print("➡️ Entrando no subcorredor")

        # Opcional: centralizar QR na imagem antes de avançar
        try:
            center_ok = self._center_qr_before_enter()
            if not center_ok:
                print("⚠️ Não foi possível centralizar o QR dentro do tempo; prosseguindo assim mesmo")
        except Exception as e:
            print(f"⚠️ Falha ao centralizar QR: {e}")

        # Avançar antes da curva, conforme config
        try:
            esp32_available = hasattr(self.basic_nav, 'mpu') and getattr(self.basic_nav.mpu, 'serial_conn', None) is not None
            if esp32_available:
                sc_cfg = NAVIGATION_CONFIG.get('subcorredor_entry', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
                forward_sec = float(sc_cfg.get('forward_seconds', 3.0))
                forward_speed = sc_cfg.get('forward_speed', None)
                velocidade = int(forward_speed) if forward_speed is not None else getattr(self, 'speed_base', 18)
                print(f"🚗 Avançando por {forward_sec:.1f}s (velocidade={velocidade})")
                self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': velocidade})
                time.sleep(forward_sec)
                self.basic_nav.parar()
            else:
                sc_cfg = NAVIGATION_CONFIG.get('subcorredor_entry', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
                forward_sec = float(sc_cfg.get('forward_seconds', 3.0))
                print(f"(simulação) avançando {forward_sec:.1f}s para frente")
                time.sleep(forward_sec)
        except Exception as e:
            print(f"❌ Falha ao avançar: {e}")
            self.basic_nav.parar()
            return False

        # Virar usando giroscópio conforme config
        sc_cfg = NAVIGATION_CONFIG.get('subcorredor_entry', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
        turn_dir = sc_cfg.get('turn_direction', 'direita')
        # Se existir configuração de ângulo, ajuste o navigation_basic
        try:
            angle_cfg = int(sc_cfg.get('turn_angle_deg', 90))
            if hasattr(self.basic_nav, 'angulo_curva'):
                self.basic_nav.angulo_curva = angle_cfg
        except Exception:
            pass

        if not self.basic_nav.virar_90_graus(turn_dir):
            return False

        print(f"✅ Entrada no subcorredor concluída (frente {sc_cfg.get('forward_seconds', 3.0)}s + curva à {turn_dir})")
        return True

    def _center_qr_before_enter(self):
        """Usa o bbox do QR atual para centralizá-lo horizontalmente na imagem antes de avançar.
        Faz pequenos pulsos de rotação e avanço até que o centro do QR esteja próximo do centro da imagem
        ou até atingir timeout. Retorna True se centralizado, False caso contrário.
        """
        try:
            cfg = NAVIGATION_CONFIG.get('qr_centering', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
            if not cfg or not cfg.get('enabled', True):
                return True

            timeout = float(cfg.get('timeout_s', 4.0))
            tol_px = int(cfg.get('tolerance_px', 24))
            rot_speed = int(cfg.get('rotate_speed', 12))
            rot_pulse = float(cfg.get('rotate_pulse_s', 0.08))
            fwd_speed_cfg = cfg.get('forward_speed', None)
            fwd_pulse = float(cfg.get('forward_pulse_s', 0.10))
            fwd_speed = int(fwd_speed_cfg) if fwd_speed_cfg is not None else int(getattr(self, 'speed_base', 40))

            start = time.time()
            last_seen = 0
            last_snap = 0.0
            # Garantir pasta de snapshots
            os.makedirs(self.snapshots_dir, exist_ok=True)

            while time.time() - start < timeout:
                # Pegar frame atual processado (garante ROI/frame reais)
                info = self.line_detector.process_frame()
                if not info or info.get('roi') is None:
                    time.sleep(0.05)
                    continue
                frame = info.get('frame_bgr') if info.get('frame_bgr') is not None else info.get('roi')

                dec = self._decode_qr_multi(frame)
                # Selecionar QR principal (maior área)
                qr_bbox = None
                max_area = -1
                for d in dec:
                    bx, by, bw, bh = d.get('bbox', (0,0,0,0))
                    area = bw * bh
                    if area > max_area and bw > 0 and bh > 0:
                        max_area = area
                        qr_bbox = (bx, by, bw, bh)

                if qr_bbox is None:
                    # Dê um passo pequeno à frente para tentar trazer o QR de volta ao campo
                    if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': fwd_speed})
                        time.sleep(fwd_pulse)
                        self.basic_nav.parar()
                    # Snapshot periódico quando não encontra QR
                    if time.time() - last_snap > 0.35 and info.get('frame_bgr') is not None:
                        try:
                            fbgr = info.get('frame_bgr').copy()
                            cv2.putText(fbgr, 'QR nao detectado', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                            cv2.imwrite(os.path.join(self.snapshots_dir, f'qr_center_none_{int(time.time()*1000)}.png'), fbgr)
                        except Exception:
                            pass
                        last_snap = time.time()
                    time.sleep(0.05)
                    continue

                h, w = frame.shape[:2]
                cx_img = w // 2
                bx, by, bw, bh = qr_bbox
                cx_qr = bx + bw // 2
                err = cx_qr - cx_img

                if abs(err) <= tol_px:
                    print(f"🎯 QR centralizado (erro {err}px <= {tol_px}px)")
                    # Snapshot de sucesso
                    try:
                        fbgr = info.get('frame_bgr') if info.get('frame_bgr') is not None else frame
                        vis = fbgr.copy()
                        cv2.rectangle(vis, (bx, by), (bx+bw, by+bh), (0,255,0), 2)
                        cv2.line(vis, (cx_img, 0), (cx_img, h), (0,255,255), 1)
                        cv2.putText(vis, f'centralizado err={err}px', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                        cv2.imwrite(os.path.join(self.snapshots_dir, f'qr_center_ok_{int(time.time()*1000)}.png'), vis)
                    except Exception:
                        pass
                    return True

                # Decidir direção do pulso de rotação (inverter devido à orientação do MPU/ESP32)
                turn_cmd = 'virar_direita' if err > 0 else 'virar_esquerda'
                # NOTA: No BasicNavigation o sentido é invertido, mas aqui enviamos direto ao ESP32
                if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                    self.basic_nav.mpu.enviar_comando(turn_cmd, {'velocidade': rot_speed})
                    time.sleep(rot_pulse)
                    self.basic_nav.parar()

                # Pequeno pulso à frente para manter QR visível
                if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                    self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': fwd_speed})
                    time.sleep(fwd_pulse)
                    self.basic_nav.parar()

                # Snapshot periódico mostrando bbox/erro
                if time.time() - last_snap > 0.35:
                    try:
                        fbgr = info.get('frame_bgr') if info.get('frame_bgr') is not None else frame
                        vis = fbgr.copy()
                        cv2.rectangle(vis, (bx, by), (bx+bw, by+bh), (0,255,255), 2)
                        cv2.line(vis, (cx_img, 0), (cx_img, h), (0,255,255), 1)
                        cv2.putText(vis, f'err={err}px', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                        cv2.imwrite(os.path.join(self.snapshots_dir, f'qr_center_try_{int(time.time()*1000)}.png'), vis)
                    except Exception:
                        pass
                    last_snap = time.time()

                last_seen = time.time()

            return False
        except Exception as e:
            print(f"Erro no centralizador de QR: {e}")
            return False

    def exit_subcorredor(self):
        """Sair do subcorredor de volta à linha principal"""
        print("⬅️ Saindo do subcorredor")
        try:
            from config import NAVIGATION_CONFIG as _NC
            exit_cfg = _NC.get('subcorredor_exit', {})
        except Exception:
            exit_cfg = {}

        strategy = str(exit_cfg.get('strategy', 'turn_until_green')).lower()
        turn_dir = str(exit_cfg.get('turn_direction', 'esquerda')).lower()
        back_dist = int(exit_cfg.get('back_distance_cm', 30))

        if strategy == 'back_and_turn':
            # Comportamento antigo: ré e virar
            if not self.basic_nav.mover_em_linha_reta(back_dist, 'tras'):
                return False
            if not self.basic_nav.virar_90_graus(turn_dir):
                return False
        elif strategy == 'turn_only':
            # Novo: apenas virar para a esquerda (ou direção configurada)
            if not self.basic_nav.virar_90_graus(turn_dir):
                return False
        elif strategy == 'turn_until_green':
            # Virar continuamente na direção indicada até detectar verde centralizado
            print(f"🔄 Virando para {turn_dir} até encontrar VERDE")
            cmd_turn = 'virar_esquerda' if turn_dir == 'esquerda' else 'virar_direita'
            # Parâmetros de detecção de verde durante a curva
            tol_px = int(_NC.get('turn', {}).get('vision', {}).get('tolerance_px', 22))
            min_area = 1200
            persist = 2
            streak = 0
            t_start = time.time()
            timeout_s = float(_NC.get('turn', {}).get('vision', {}).get('timeout_s', 8.0))
            while time.time() - t_start < timeout_s:
                # Aplicar um pequeno pulso de giro
                if getattr(self.basic_nav, 'mpu', None) and getattr(self.basic_nav.mpu, 'serial_conn', None):
                    self.basic_nav.mpu.enviar_comando(cmd_turn, {'velocidade': int(_NC.get('turn', {}).get('vision', {}).get('speed_slow', 8))})
                    time.sleep(float(_NC.get('turn', {}).get('vision', {}).get('creep_pulse_s', 0.06)))
                    self.basic_nav.parar()
                # Capturar frame e checar verde
                f = self.line_detector.capture_frame()
                if f is None:
                    continue
                fbgr = cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
                g = self._detect_green_square(fbgr)
                if g.get('detected') and g.get('area', 0) >= min_area:
                    # Centro do verde vs centro da imagem
                    h, w = fbgr.shape[:2]
                    cx_img = w // 2
                    cx_g = g['center'][0]
                    err = abs(cx_g - cx_img)
                    if err <= tol_px:
                        streak += 1
                        if streak >= persist:
                            print("✅ Verde centrado; encerrando curva")
                            break
                    else:
                        streak = 0
                else:
                    streak = 0
                time.sleep(0.05)
            # Parar após o loop
            self.basic_nav.parar()

        print("✅ Saída do subcorredor concluída")
        return True

    def navigate_to_delivery_point(self):
        """Navegar até o ponto de entrega"""
        print("📦 Navegando até ponto de entrega")

        qr_delivery = "Entrega"
        start_time = time.time()

        while not self.stop_event.is_set():
            # Seguir linha
            if not self.follow_line_step():
                break

            # Verificar QR code de entrega
            qr_found = self.check_qr_codes()
            if qr_found == qr_delivery:
                print("✅ Ponto de entrega encontrado!")
                return True

            # Timeout
            if time.time() - start_time > 60:  # 1 minuto máximo
                print("⏰ Timeout na navegação até entrega")
                break

            time.sleep(0.1)

        return False

    def start_line_following(self):
        """Iniciar seguimento de linha em thread separada"""
        if self.following_line:
            print("⚠️ Seguimento de linha já ativo")
            return

        self.stop_event.clear()
        self.following_line = True

        self.navigation_thread = threading.Thread(target=self._line_following_loop)
        self.navigation_thread.daemon = True
        self.navigation_thread.start()

        print("▶️ Seguimento de linha iniciado")

    def stop_line_following(self):
        """Parar seguimento de linha"""
        if not self.following_line:
            return

        self.stop_event.set()
        self.following_line = False

        if self.navigation_thread:
            self.navigation_thread.join(timeout=2)

        self.basic_nav.parar()

        # Fechar janela visual se estiver aberta
        if self.visual_feedback:
            try:
                cv2.destroyWindow(self.visual_window_name)
            except:
                pass

        print("⏹️ Seguimento de linha parado")

    def _line_following_loop(self):
        """Loop principal de seguimento de linha com timing adaptativo"""
        print("🔄 Iniciando loop de seguimento de linha")

        while not self.stop_event.is_set():
            try:
                success = self.follow_line_step()
                if success:
                    # Timing adaptativo baseado na detecção de QR
                    if self.qr_detected_recently:
                        time.sleep(0.5)  # Mais lento quando detecta QR recentemente
                    else:
                        time.sleep(0.15)  # Normal
                else:
                    time.sleep(0.3)  # Pausa maior se não detectar linha

            except Exception as e:
                print(f"Erro no loop de seguimento: {e}")
                break

        print("🔄 Loop de seguimento finalizado")

    def test_line_following(self, duration=10):
        """Testar seguimento de linha por tempo determinado"""
        print(f"🧪 Testando seguimento de linha por {duration} segundos")

        self.start_line_following()
        time.sleep(duration)
        self.stop_line_following()

        print("✅ Teste concluído")

    def calibrate_green_square(self):
        """Calibrar parâmetros de detecção do quadrado verde com interface OpenCV"""
        print("🎨 CALIBRAÇÃO DO QUADRADO VERDE")
        print("=" * 40)

        # Verificar se o detector de linha já está inicializado
        if self.line_detector.picam2 is None:
            print("❌ Detector de linha não inicializado. Execute a inicialização primeiro.")
            return

        print("📷 Iniciando captura contínua para calibração...")
        print("Use os controles deslizantes para ajustar.")
        print("Pressione 'ESC' para sair e salvar os parâmetros.")

        # Iniciar captura contínua
        if not self.line_detector.start_continuous_capture():
            print("❌ Falha ao iniciar captura contínua")
            return

        try:
            # Criar janela de controle
            cv2.namedWindow('Controles HSV', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Controles HSV', 400, 200)

            # Parâmetros iniciais
            params = {
                'H_min': 30, 'H_max': 90,
                'S_min': 30, 'S_max': 255,
                'V_min': 30, 'V_max': 255
            }

            # Criar trackbars
            cv2.createTrackbar('H Min', 'Controles HSV', params['H_min'], 179, lambda x: None)
            cv2.createTrackbar('H Max', 'Controles HSV', params['H_max'], 179, lambda x: None)
            cv2.createTrackbar('S Min', 'Controles HSV', params['S_min'], 255, lambda x: None)
            cv2.createTrackbar('S Max', 'Controles HSV', params['S_max'], 255, lambda x: None)
            cv2.createTrackbar('V Min', 'Controles HSV', params['V_min'], 255, lambda x: None)
            cv2.createTrackbar('V Max', 'Controles HSV', params['V_max'], 255, lambda x: None)

            while True:
                # Capturar frame usando captura contínua
                frame = self.line_detector.capture_continuous_frame()
                if frame is None:
                    continue

                # Ler valores dos trackbars
                params['H_min'] = cv2.getTrackbarPos('H Min', 'Controles HSV')
                params['H_max'] = cv2.getTrackbarPos('H Max', 'Controles HSV')
                params['S_min'] = cv2.getTrackbarPos('S Min', 'Controles HSV')
                params['S_max'] = cv2.getTrackbarPos('S Max', 'Controles HSV')
                params['V_min'] = cv2.getTrackbarPos('V Min', 'Controles HSV')
                params['V_max'] = cv2.getTrackbarPos('V Max', 'Controles HSV')

                # Aplicar detecção
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower = np.array([params['H_min'], params['S_min'], params['V_min']])
                upper = np.array([params['H_max'], params['S_max'], params['V_max']])
                mask = cv2.inRange(hsv, lower, upper)

                # Operações morfológicas
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

                # Detectar contornos verdes
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                green_squares = 0

                result_frame = frame.copy()
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 800:
                        x, y, w, h = cv2.boundingRect(contour)
                        peri = cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
                        vertices = len(approx)
                        aspect_ratio = float(w) / h if h > 0 else 999
                        extent = area / float(w * h) if (w * h) > 0 else 0.0

                        # Candidato (amarelo)
                        cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 255), 1)
                        cv2.putText(result_frame, f"v{vertices} r{aspect_ratio:.2f} e{extent:.2f}", (x, max(12, y-4)),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

                        # Aceitar mais permissivo para destacar (verde)
                        if 4 <= vertices <= 8 and 0.6 <= aspect_ratio <= 1.6 and extent >= 0.45 and w > 50 and h > 50:
                            cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                            cv2.putText(result_frame, f"VERDE {w}x{h}", (x, y-10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            green_squares += 1

                # Combinar imagem original e máscara lado a lado
                height, width = frame.shape[:2]
                combined = np.zeros((height, width*2, 3), dtype=np.uint8)

                # Lado esquerdo: imagem original com detecções
                combined[:, :width] = result_frame

                # Lado direito: máscara em cores
                mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                combined[:, width:] = mask_colored

                # Adicionar linha divisória
                cv2.line(combined, (width, 0), (width, height), (255, 255, 255), 2)

                # Adicionar títulos
                cv2.putText(combined, "ORIGINAL + DETECCOES", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(combined, "MASCARA VERDE", (width + 10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # Adicionar informações dos parâmetros
                info_text = [
                    f"H: {params['H_min']}-{params['H_max']}",
                    f"S: {params['S_min']}-{params['S_max']}",
                    f"V: {params['V_min']}-{params['V_max']}",
                    f"Quadrados: {green_squares}"
                ]

                for i, text in enumerate(info_text):
                    cv2.putText(combined, text, (10, height - 40 + i*25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Adicionar instruções
                cv2.putText(combined, "ESC: Salvar e Sair", (width - 200, height - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                # Mostrar imagem combinada
                cv2.imshow('Calibracao Verde - Original | Mascara', combined)

                # Verificar tecla
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break

        except Exception as e:
            print(f"❌ Erro na calibração: {e}")

        finally:
            cv2.destroyAllWindows()
            self.line_detector.stop_continuous_capture()

        print("✅ Calibração concluída")
        print(f"🔧 Parâmetros finais recomendados:")
        print(f"   Hue: {params['H_min']}-{params['H_max']}")
        print(f"   Saturation: {params['S_min']}-{params['S_max']}")
        print(f"   Value: {params['V_min']}-{params['V_max']}")

        # Perguntar se quer salvar
        try:
            save = input("\n💾 Salvar parâmetros no código? (s/n): ").lower().strip()
            if save == 's':
                self._update_green_detection_params(params)
                print("✅ Parâmetros salvos! Reinicie o programa para aplicar.")
            else:
                print("ℹ️ Parâmetros não salvos. Use-os manualmente no código.")
        except:
            print("ℹ️ Modo não-interativo - parâmetros não salvos automaticamente.")

    def _update_green_detection_params(self, params):
        """Atualizar parâmetros de detecção no código (simulado)"""
        print("🔧 Para aplicar permanentemente, atualize estes valores no método _detect_green_square:")
        print(f"   lower_green = np.array([{params['H_min']}, {params['S_min']}, {params['V_min']})")
        print(f"   upper_green = np.array([{params['H_max']}, {params['S_max']}, {params['V_max']})")
        print("   # Tamanho mínimo mantido em 50 pixels")

        # Aqui poderia escrever em um arquivo de configuração
        # Por enquanto, apenas mostra os valores

    def cleanup(self):
        """Limpar recursos"""
        self.stop_line_following()
        self.line_detector.cleanup()
        # QR detector não tem cleanup
        print("🧹 Recursos de navegação liberados")

    def start_visual_preview(self):
        """Pré-visualização visual (mostra linha, quadrado verde e QR sem mover motores)."""
        print("🎥 PRÉ-VISUALIZAÇÃO (Item 8): Linha + Quadrado Verde + QR")
        # Garantir janela
        self.enable_visual_feedback()

        # Verificar inicialização de câmera/detector
        try:
            if self.line_detector.picam2 is None:
                if not self.line_detector.initialize():
                    print("❌ Falha ao inicializar câmera para pré-visualização")
                    return
        except Exception:
            # Se a API do detector não tiver esse atributo, assumimos que initialize já foi chamado
            pass

        try:
            while True:
                line_info = self.line_detector.process_frame()
                if not line_info:
                    # Nada a exibir nesta iteração
                    continue

                frame = line_info.get('roi')
                if frame is None:
                    # Se não houver ROI, não conseguimos exibir corretamente nesta iteração
                    continue

                # Detectar quadrado verde na ROI
                green_square = self._detect_green_square(frame)
                line_info['green_square'] = green_square

                # Detectar QR codes na ROI
                qr_list = []
                try:
                    results = self._decode_qr_multi(frame)
                    for res in results:
                        qr_list.append(res)
                        print(f"🔎 QR (preview): {res.get('data','')}")
                except Exception:
                    pass

                line_info['qr_codes'] = qr_list

                # Atualizar alguns status mínimos do painel
                self.status_info.update({
                    'linha_detectada': bool(line_info.get('detected')),
                    'confianca': line_info.get('confidence', 0.0),
                    'qr_detectado': bool(qr_list),
                    'velocidade': 0,
                    'direcao': 'preview'
                })

                # Mostrar
                self.update_visual_frame(frame, line_info)

                # Tecla para sair
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break

        except KeyboardInterrupt:
            print("⛔ Pré-visualização interrompida")
        finally:
            self.disable_visual_feedback()

def main():
    """Função principal para teste"""
    print("NAVEGACAO SEGUINDO LINHA PRETA")
    print("=" * 35)

    # Criar navegação
    nav = LineFollowingNavigation()

    # Inicializar
    if not nav.initialize():
        return

    # Menu de teste
    while True:
        print("\n" + "="*50)
        print("🎮 MENU DE NAVEGAÇÃO POR LINHA")
        print("="*50)
        print("1. Teste básico de seguimento (10s)")
        print("2. Navegar até subcorredor 01")
        print("3. Entrar no subcorredor")
        print("4. Sair do subcorredor")
        print("5. Ir para ponto de entrega")
        print("6. Mostrar status")
        print("7. Parar motores")
        print("8. Ativar feedback visual")
        print("9. Desativar feedback visual")
        print("10. Calibrar quadrado verde")
        print("0. Sair")
        print("="*50)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                nav.test_line_following(10)
            elif opcao == '2':
                nav.navigate_to_intersection("01")
            elif opcao == '3':
                nav.enter_subcorredor()
            elif opcao == '4':
                nav.exit_subcorredor()
            elif opcao == '5':
                nav.navigate_to_delivery_point()
            elif opcao == '6':
                nav.basic_nav.mostrar_status()
            elif opcao == '7':
                nav.basic_nav.parar()
                print("🛑 Motores parados")
            elif opcao == '8':
                nav.start_visual_preview()
            elif opcao == '9':
                nav.disable_visual_feedback()
            elif opcao == '10':
                nav.calibrate_green_square()
            elif opcao == '0':
                nav.cleanup()
                print("👋 Saindo...")
                break
            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            nav.cleanup()
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            nav.cleanup()

if __name__ == "__main__":
    main()