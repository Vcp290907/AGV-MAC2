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
from config import get_esp32_port
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
        # Velocidades mais baixas para melhorar leitura de QR em movimento
        self.speed_base = 50  # antes 65
        self.speed_min = 20   # antes 30
        self.speed_max = 70   # antes 85

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

            # Obter correção de direção calculada pelo detector
            steering_correction = line_info['steering_correction']
            error_pixels = line_info['center'] - (self.line_detector.width // 2)

            print(f"📏 Centro linha: {line_info['center']}, Erro: {error_pixels}px, Correção: {steering_correction:.3f}")

            # QR code SÓ é lido quando quadrado verde é detectado
            qr_content = None
            qr_source = None  # 'green_square' ou 'line_detection'
            # Verificar disponibilidade do ESP32 apenas uma vez
            esp32_available = hasattr(self.basic_nav, 'mpu') and getattr(self.basic_nav.mpu, 'serial_conn', None) is not None

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
                        'confidence': refreshed.get('confidence', line_info.get('confidence')),
                        'steering_correction': refreshed.get('steering_correction', line_info.get('steering_correction'))
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
                            # Imprimir apenas se for diferente do último ou passou tempo suficiente
                            if qr_content != self.last_qr_text or (time.time() - self.last_qr_time) > 2.0:
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

                if abs(steering_correction) < 0.05:
                    # Movimento reto normal - manter por mais tempo
                    print("➡️ Movimento reto")
                    direcao = 'frente'
                    velocidade = base_speed
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': base_speed})
                elif abs(steering_correction) < 0.3:
                    # Correção leve - movimento para frente com velocidade reduzida
                    reduced_speed = max(self.speed_min, base_speed - int(abs(steering_correction) * 10))
                    print(f"🔄 Correção leve ({steering_correction:.3f}) - velocidade reduzida: {reduced_speed}")
                    direcao = 'frente_corrigido'
                    velocidade = reduced_speed
                    if esp32_available:
                        self.basic_nav.mpu.enviar_comando('mover_frente', {'velocidade': reduced_speed})
                else:
                    # Correção necessária - impulso de correção mais rápido
                    # INVERTER A DIREÇÃO: steering_correction > 0 significa linha à direita, então virar para ESQUERDA
                    correction_speed = max(8, min(15, int(abs(steering_correction) * 12)))  # Velocidade maior

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
                        time.sleep(0.02)  # Tempo ainda menor para correção mais rápida
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

        start_time = time.time()
        qr_found = None

        while not self.stop_event.is_set():
            # Seguir linha
            if not self.follow_line_step():
                break

            # Verificar interseção
            if self.detect_intersection():
                print("🔀 Interseção encontrada!")

                # Verificar QR code na interseção
                qr_found = self.check_qr_codes()

                if qr_found and qr_found == f"Corredor01_{target_subcorredor}":
                    print(f"✅ Subcorredor correto encontrado: {qr_found}")
                    break
                else:
                    print(f"⚠️ Subcorredor errado ou QR não encontrado: {qr_found}")
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

        # Virar 90° para direita (assumindo layout em T)
        if not self.basic_nav.virar_90_graus('direita'):
            return False

        # Seguir em frente por uma distância
        distance_to_shelf = 30  # cm até a prateleira
        if not self.basic_nav.mover_em_linha_reta(distance_to_shelf, 'frente'):
            return False

        print("✅ Entrada no subcorredor concluída")
        return True

    def exit_subcorredor(self):
        """Sair do subcorredor de volta à linha principal"""
        print("⬅️ Saindo do subcorredor")

        # Dar ré até a linha principal
        if not self.basic_nav.mover_em_linha_reta(30, 'tras'):
            return False

        # Virar 90° para esquerda para voltar à linha
        if not self.basic_nav.virar_90_graus('esquerda'):
            return False

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