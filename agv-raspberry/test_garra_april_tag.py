import time
import numpy as np
import cv2
from picamera2 import Picamera2
from esp32_control import connect_esp32_garra, move_servos_esp32
from april_tag_detector import AprilTagDetector
import arm_pick_config as APC
from arm_inverse_kinematics import ArmInverseKinematics

class DynamicArmController:
    def __init__(self, target_tag_ids=[10]):
        self.target_tag_ids = target_tag_ids
        self.tag_size_m = 0.03  # 3cm

        # Inicializar câmera
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(
            main={"format": 'RGB888', "size": (1280, 720)}
        ))
        self.picam2.start()

        # Inicializar detector de AprilTags (usa calibração existente)
        self.detector = AprilTagDetector(
            camera_index=0,
            calibration_file='camera_calib_charuco.json',
            tag_size_m=self.tag_size_m
        )

        # Conectar ESP32 (garra)
        if not connect_esp32_garra():
            raise RuntimeError("❌ Falha ESP32 Garra")

        # Calibração e mapeamentos de servo (carregados de arm_pick_config)
        self.GARRA_OPEN = APC.GARRA_OPEN
        self.GARRA_CLOSED = APC.GARRA_CLOSED
        self.BASE_SHELF = dict(APC.BASE_SHELF)
        self.BASE_FAR   = dict(APC.BASE_FAR)
        self.Z_NEAR = APC.Z_NEAR
        self.Z_FAR  = APC.Z_FAR
        self.GIRO_BASE = APC.GIRO_BASE
        self.GIRO_PER_DEG = APC.GIRO_PER_DEG

        # Parâmetros de alinhamento dinâmico
        self.TARGET_Z = APC.TARGET_Z
        self.YAW_TOL_DEG = APC.YAW_TOL_DEG
        self.Z_TOL_M = APC.Z_TOL_M
        self.K_GIRO = APC.K_GIRO
        self.MAX_GIRO_STEP = APC.MAX_GIRO_STEP
        self.SMOOTH = APC.SMOOTH

        # Tag da garra e offset até a ponta dos dedos (metros)
        self.GRIPPER_TAG_ID = int(getattr(APC, 'GRIPPER_TAG_ID', 9))
        self.OFFSET_GRIPPER_TO_FINGERS = np.array(getattr(APC, 'OFFSET_GRIPPER_TO_FINGERS', [0.0, 0.0, 0.05]), dtype=float)

        # Garantir que a lista de alvos não contenha a tag da garra
        # self.target_tag_ids = [tid for tid in self.target_tag_ids if tid != self.GRIPPER_TAG_ID]

        # Limites e calibração por junta
        self.JOINT_LIMITS = dict(getattr(APC, 'JOINT_LIMITS', {}))
        self.JOINT_CALIB = dict(getattr(APC, 'JOINT_CALIB', {}))

        # Estado inicial de ângulos (aplica limites e calibração)
        self.current_angles = self._apply_calibration_and_limits(dict(self.BASE_FAR), warn=False)

        # Resolvedor de cinemática inversa
        self.ik_solver = ArmInverseKinematics(link1_len=0.13, link2_len=0.11, link3_len=0.05)

        print("✅ Sistema dinâmico inicializado")

    def run_cycle(self):
        """Ciclo completo: detectar tags e alinhar dinamicamente até pegar o item"""

        # 1) Capturar frame atual
        frame = self.picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite('current_frame.jpg', frame_bgr)

        # 2) Detectar AprilTags no frame
        detections = self.detect_april_tags_from_frame(frame_bgr)
        if not detections:
            return 0

        # 3) Verificar se a tag da garra está visível; se não, mover para posição conhecida
        gripper_visible = any(d['id'] == self.GRIPPER_TAG_ID for d in detections)
        if not gripper_visible:
            print(f"⚠️ Tag da garra ({self.GRIPPER_TAG_ID}) não visível; movendo para posição conhecida...")
            self.move_to_gripper_known_position()
            # Após mover, tentar detectar novamente
            frame = self.picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            detections = self.detect_april_tags_from_frame(frame_bgr)
            gripper_visible = any(d['id'] == self.GRIPPER_TAG_ID for d in detections)
            if not gripper_visible:
                print("❌ Tag da garra ainda não visível após mover; abortando")
                return 0

        # Verificar se a tag alvo (10) está visível
        target_visible = any(d['id'] == 10 for d in detections)
        if not target_visible:
            print("⚠️ Tag alvo (10) não visível; aguardando...")
            return 0

        # 4) Selecionar a melhor tag alvo (menor Z, se disponível)
        #    Preferência: IDs da lista; Fallback: qualquer tag que NÃO seja a tag da garra
        ids_all = [d['id'] for d in detections if 'id' in d]
        print(f"🔎 IDs detectados no frame: {ids_all}")

        # Candidatas por target list (exclui a tag da garra)
        candidates = [d for d in detections if d['id'] in self.target_tag_ids and d['id'] != self.GRIPPER_TAG_ID]

        best = None
        best_z = 1e9
        for det in candidates:
            pose = det.get('pose')
            if pose and pose[1] is not None:
                z = float(pose[1][2])
                if z < best_z:
                    best = det
                    best_z = z
            elif best is None:
                best = det  # fallback sem pose

        if not best:
            print("⛔ Nenhuma tag candidata válida neste frame")
            return 0

        # Verificar se a tag da garra (9) está visível
        gripper_det = next((d for d in detections if d['id'] == self.GRIPPER_TAG_ID), None)
        if not gripper_det:
            print(f"⚠️ Tag da garra ({self.GRIPPER_TAG_ID}) não detectada; pulando este ciclo")
            return 0

        # 5) Executar rotina de alinhamento e coleta
        ok = self.align_and_grab(best, frame_bgr.shape[1], frame_bgr.shape[0])
        return 1 if ok else 0

    def detect_april_tags_from_frame(self, frame_bgr):
        """Detecta AprilTags no frame usando AprilTagDetector (exatamente como no debug_apriltag_live.py)"""
        # Usa exatamente a mesma chamada do debug_apriltag_live.py
        dets = self.detector.detect_in_frame(
            frame_bgr,
            requested_tag_ids=None,      # detectar todas
            save_photo=True,             # salva imagem anotada
            photo_prefix='tag_frame',
            scale_factor=1.0
        )
        ids = [d.get('id') for d in dets] if dets else []
        print(f"📷 detect_in_frame -> IDs: {ids}")

        results = []
        for d in dets:
            corners = d.get('corners')
            if corners is not None:
                cx, cy = corners.mean(axis=0).astype(int).tolist()
            else:
                cx, cy = None, None
            results.append({
                'id': d.get('id'),
                'family': 'tag36h11',
                'center': [cx, cy],
                'pose': (d.get('rvec'), d.get('tvec'))  # (rvec, tvec)
            })
        return results

    def calculate_arm_angles_from_pose(self, pose, tag_id=None):
        """Calcula ângulos do braço a partir de (rvec, tvec) usando mapeamento simples"""
        # Fallback: se sem pose, usar base de estante
        if not pose or pose[1] is None:
            return {
                "giro": int(np.clip(self.GIRO_BASE, 0, 180)),
                "um": int(np.clip(self.BASE_SHELF["um"], 0, 180)),
                "dois": int(np.clip(self.BASE_SHELF["dois"], 0, 180)),
                "garra": self.GARRA_OPEN,
                "servo3": self.BASE_SHELF["servo3"]
            }

        rvec, tvec = pose
        x = float(tvec[0]); y = float(tvec[1]); z = float(tvec[2])
        print(f"📐 Pose: X={x:.3f} Y={y:.3f} Z={z:.3f} m")

        # Giro baseado no azimute para o alvo
        yaw_deg = float(np.degrees(np.arctan2(x, z)))
        giro = self.GIRO_BASE + self.GIRO_PER_DEG * yaw_deg

        # Interpolação entre duas poses por distância Z
        z_clamped = float(np.clip(z, self.Z_NEAR, self.Z_FAR))
        s = (z_clamped - self.Z_NEAR) / (self.Z_FAR - self.Z_NEAR + 1e-9)
        um = self.BASE_SHELF["um"] + s * (self.BASE_FAR["um"] - self.BASE_SHELF["um"])
        dois = self.BASE_SHELF["dois"] + s * (self.BASE_FAR["dois"] - self.BASE_SHELF["dois"])

        angles = {
            "giro": int(np.clip(round(giro), 0, 180)),
            "um": int(np.clip(round(um), 0, 180)),
            "dois": int(np.clip(round(dois), 0, 180)),
            "garra": self.GARRA_OPEN,
            "servo3": self.BASE_SHELF["servo3"]
        }
        # Aplica limites/calibração para evitar posições perigosas antes de enviar
        filtered = self._apply_calibration_and_limits(angles, warn=False)
        print(f"🔧 Ângulos (após limites): {filtered}")
        return filtered

    def _apply_calibration_and_limits(self, angles, warn=True):
        """Aplica inversão/offset por junta e limita pelos JOINT_LIMITS; retorna dict pronto para enviar."""
        result = {}
        for k, v in angles.items():
            try:
                val = float(v)
            except Exception:
                continue

            # Calibração (invert, offset)
            calib = self.JOINT_CALIB.get(k, {})
            if calib.get("invert"):
                val = 180.0 - val
            val += float(calib.get("offset", 0.0))

            # Limites específicos por junta
            lim = self.JOINT_LIMITS.get(k, (0, 180))
            v_before = val
            val = float(np.clip(val, lim[0], lim[1]))
            if warn and abs(val - v_before) > 1e-6:
                print(f"⚠️ Clamp {k}: {v_before:.1f} -> {val:.1f} (lim {lim[0]}..{lim[1]})")

            result[k] = int(round(val))
        return result

    def _send_angles(self, angles, wait=0.25):
        # Mescla com ângulos atuais, aplica calibração/limites, aplica passo máximo por junta e envia
        if not hasattr(self, 'current_angles'):
            self.current_angles = {}
        desired = dict(self.current_angles)
        desired.update(angles)
        # Converte para espaço de servo (aplica invert/offset/limites)
        desired = self._apply_calibration_and_limits(desired, warn=True)

        # Limitar passo por junta para evitar movimentos bruscos/danos
        max_step_cfg = getattr(APC, 'JOINT_MAX_STEP', {})
        limited = {}
        for k, tgt in desired.items():
            cur = int(self.current_angles.get(k, tgt))
            max_step = int(max_step_cfg.get(k, 10))
            delta = int(tgt) - cur
            if abs(delta) > max_step:
                tgt = cur + (max_step if delta > 0 else -max_step)
            # Garantir faixa 0..180 (já deve estar limítada, é redundância segura)
            limited[k] = int(np.clip(tgt, 0, 180))

        move_servos_esp32(limited)
        self.current_angles = limited
        time.sleep(wait)

    def _blend(self, a, b, s):
        return (1 - s) * a + s * b

    def align_and_grab(self, initial_det, frame_w, frame_h):
        """
        Usa cinemática inversa para posicionar diretamente a ponta da garra no item.
        """
        tag_item_id = initial_det['id']
        max_iters = 15
        aligned = False

        print("🎯 Iniciando controle com cinemática inversa...")

        for i in range(max_iters):
            # Captura e detecção
            frame = self.picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            dets_all = self.detector.detect_in_frame(
                frame_bgr, requested_tag_ids=None, save_photo=False, photo_prefix='tag_ik', scale_factor=1.0
            )

            # Encontrar tags
            det_item = None
            det_grip = None
            for d in dets_all:
                if d.get('id') == tag_item_id:
                    det_item = d
                if d.get('id') == self.GRIPPER_TAG_ID:
                    det_grip = d

            if det_item is None or det_item.get('tvec') is None:
                print(f"⚠️ Tag do item ({tag_item_id}) não visível")
                time.sleep(0.1)
                continue

            # Posição alvo: centro da tag do item
            target_x = float(det_item['tvec'][0])
            target_y = float(det_item['tvec'][1])
            target_z = float(det_item['tvec'][2])

            print(f"🎯 it:{i} Alvo bruto: X={target_x:.4f} Y={target_y:.4f} Z={target_z:.4f}")

            # Modo manual: usar coordenadas fixas para teste
            # Substitua estes valores pelas coordenadas que você medir manualmente
            target_x = -0.02  # coordenada X medida
            target_y = 0.08   # coordenada Y medida
            target_z = 0.10   # coordenada Z medida (um pouco acima do item)

            print(f"🎯 it:{i} Alvo manual: X={target_x:.4f} Y={target_y:.4f} Z={target_z:.4f}")

            # Resolver cinemática inversa para alcançar o alvo
            ik_angles = self.ik_solver.inverse_kinematics(target_x, target_y, target_z)

            if ik_angles is None:
                print("❌ Posição inalcançável")
                continue

            theta_base, theta_shoulder, theta_elbow = ik_angles

            # Validar solução (tolerância mais frouxa para começar)
            if not self.ik_solver.validate_solution(theta_base, theta_shoulder, theta_elbow,
                                                    target_x, target_y, target_z, tolerance=0.5):
                print("⚠️ Solução IK inválida, pulando...")
                continue

            # Verificar se a solução está dentro dos limites do braço
            # Permitir ângulos maiores para posições mais estendidas
            if theta_elbow < -150 or theta_elbow > 150:
                print(f"⚠️ Ângulo do cotovelo fora do limite: {theta_elbow:.1f}°, pulando...")
                continue

            # Converter para formato do controlador
            # Aplicar offset/calibração se necessário
            ik_angles_dict = {
                "giro": theta_base,
                "um": theta_shoulder,
                "dois": theta_elbow,
                "garra": self.GARRA_OPEN,
                "servo3": self.BASE_SHELF["servo3"]
            }

            # Aplicar calibração aos ângulos IK
            ik_angles_dict = self._apply_calibration_and_limits(ik_angles_dict, warn=True)

            print(f"🔧 IK bruto: giro={theta_base:.2f}° um={theta_shoulder:.2f}° dois={theta_elbow:.2f}°")
            print(f"🔧 IK calibrado: giro={ik_angles_dict['giro']:.2f}° um={ik_angles_dict['um']:.2f}° dois={ik_angles_dict['dois']:.2f}°")

            # Aplicar ângulos calculados (sempre mover para garantir precisão)
            # Mas limitar o movimento para evitar danos, especialmente o giro
            current_angles = dict(self.current_angles)
            limited_angles = {}
            for k, new_val in ik_angles_dict.items():
                if k in current_angles:
                    diff = abs(new_val - current_angles[k])
                    max_step = 0.5 if k == "giro" else 2  # giro ainda mais lento
                    if diff > max_step:
                        direction = 1 if new_val > current_angles[k] else -1
                        limited_angles[k] = current_angles[k] + direction * max_step
                    else:
                        limited_angles[k] = new_val
                else:
                    limited_angles[k] = new_val

            self._send_angles(limited_angles, wait=0.5)  # espera maior
            print("🔄 Movendo braço para nova posição...")

            # Verificar se chegou perto o suficiente
            # (simplificado: assumir que se conseguiu resolver IK e aplicar, está próximo)
            time.sleep(0.3)  # esperar movimento

            # Verificação final: ver se a ponta dos dedos está próxima do item
            if det_grip is not None and det_grip.get('tvec') is not None:
                grip_pos = np.array(det_grip['tvec'])
                fingers_pos = grip_pos + self.OFFSET_GRIPPER_TO_FINGERS
                item_pos = np.array(det_item['tvec'])
                distance = np.linalg.norm(fingers_pos - item_pos)

                print(f"📏 Distância dedos↔item: {distance:.4f}m (grip: {grip_pos}, fingers: {fingers_pos}, item: {item_pos})")

                if distance <= 0.01:  # 1cm de tolerância para os dedos (mais preciso)
                    if not hasattr(self, '_close_count'):
                        self._close_count = 0
                    self._close_count += 1
                    if self._close_count >= 5:  # aumentado para 5 confirmações
                        aligned = True
                        print("✅ Dedos posicionados no item! Fechando garra...")
                        break
                else:
                    if hasattr(self, '_close_count'):
                        self._close_count = 0

        if not aligned:
            print("❌ Não conseguiu posicionar a garra")
            return False

        # Fechar garra
        self._send_angles({"garra": self.GARRA_CLOSED}, wait=1.5)
        print("🗜️ Item pego!")
        self.return_arm_to_home()
        return True

    def move_to_gripper_known_position(self):
        """Move o braço para uma posição conhecida onde a tag da garra fica visível na câmera."""
        # Posição conhecida: braço estendido para frente, garra aberta, para que a tag fique na câmera
        # Ajuste estes valores para que a tag da garra apareça no centro da câmera
        known_angles = {
            "giro": 30,    # centralizado - ajuste se a tag aparece deslocada lateralmente
            "um": 50,      # ombro mais baixo - ajuste para profundidade
            "dois": 100,   # cotovelo mais baixo - ajuste para extensão
            "garra": self.GARRA_OPEN,  # aberta para visibilidade
            "servo3": 33
        }
        self._send_angles(known_angles, wait=1.5)  # tempo maior para movimento maior
        print("📍 Braço movido para posição conhecida (tag da garra visível)")

    def return_arm_to_home(self):
        """Retorna braço à posição inicial segura (usa BASE_FAR e mantém garra atual/fechada)"""
        home_angles = dict(self.BASE_FAR)
        # mantém estado atual da garra ou fecha por segurança
        home_angles["garra"] = int(self.current_angles.get("garra", self.GARRA_CLOSED))
        self._send_angles(home_angles, wait=0.6)
        print("🏠 Braço retornado à posição inicial segura")

    def close(self):
        """Limpa recursos"""
        try:
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
        finally:
            try:
                if hasattr(self, 'detector') and self.detector:
                    self.detector.close()
            except Exception:
                pass

# Simulador virtual 3D do braço para calibração segura
class VirtualArmSimulator3D:
    def __init__(self):
        self.ik_solver = ArmInverseKinematics(link1_len=0.13, link2_len=0.11, link3_len=0.05)
        self.current_position = {"x": 0.0, "y": 0.08, "z": 0.10}  # Posição inicial simulada

        # Inicializar visualização 3D
        self.fig = None
        self.ax = None
        self.init_3d_plot()

    def init_3d_plot(self):
        """Inicializa o plot 3D"""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            plt.ion()  # Modo interativo
            self.fig = plt.figure(figsize=(10, 8))
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.ax.set_xlabel('X (m)')
            self.ax.set_ylabel('Y (m)')
            self.ax.set_zlabel('Z (m)')
            self.ax.set_title('Simulador 3D do Braço Robótico')
            self.ax.set_xlim(-0.3, 0.3)
            self.ax.set_ylim(-0.3, 0.3)
            self.ax.set_zlim(0, 0.4)
            plt.draw()
        except ImportError:
            print("❌ Matplotlib não disponível. Instale com: pip install matplotlib")
            self.fig = None

    def update_3d_plot(self, joint_positions, target_pos=None):
        """Atualiza a visualização 3D"""
        if self.ax is None:
            return

        self.ax.clear()
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        self.ax.set_title('Simulador 3D do Braço Robótico')
        self.ax.set_xlim(-0.3, 0.3)
        self.ax.set_ylim(-0.3, 0.3)
        self.ax.set_zlim(0, 0.4)

        # Desenhar links do braço
        if len(joint_positions) >= 4:
            p0, p1, p2, p3 = joint_positions[:4]

            # Links
            self.ax.plot([p0[0], p1[0]], [p0[1], p1[1]], [p0[2], p1[2]], 'r-', linewidth=5, label='Link 1 (Base→Ombro)')
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], 'g-', linewidth=5, label='Link 2 (Ombro→Cotovelo)')
            self.ax.plot([p2[0], p3[0]], [p2[1], p3[1]], [p2[2], p3[2]], 'b-', linewidth=4, label='Link 3 (Cotovelo→Garra)')

            # Juntas
            self.ax.scatter(*p0, color='black', s=100, label='Base')
            self.ax.scatter(*p1, color='red', s=80, label='Ombro')
            self.ax.scatter(*p2, color='green', s=80, label='Cotovelo')
            self.ax.scatter(*p3, color='blue', s=80, label='Garra')

            # Posição alvo
            if target_pos:
                self.ax.scatter(*target_pos, color='orange', s=100, marker='*', label='Alvo')

        self.ax.legend()
        self.ax.grid(True)
        plt.draw()
        plt.pause(0.1)

    def simulate_position(self, x, y, z):
        """Simula o movimento do braço para uma posição XYZ com visualização 3D"""
        angles = self.ik_solver.inverse_kinematics(x, y, z)
        if angles is None:
            return None, "Posição inalcançável"

        theta_base, theta_shoulder, theta_elbow = angles

        # Validar limites
        if theta_elbow < -150 or theta_elbow > 150:
            return None, f"Ângulo do cotovelo fora do limite: {theta_elbow:.1f}°"

        # Calcular posições das juntas para visualização 3D
        joint_positions = self.calculate_joint_positions_3d(theta_base, theta_shoulder, theta_elbow)

        # Atualizar visualização 3D
        self.update_3d_plot(joint_positions, target_pos=(x, y, z))

        # Calcular posição forward kinematics para validação
        fk_pos = self.ik_solver.forward_kinematics(theta_base, theta_shoulder, theta_elbow)

        return {
            "angles": {"giro": theta_base, "um": theta_shoulder, "dois": theta_elbow},
            "position": {"x": fk_pos[0], "y": fk_pos[1], "z": fk_pos[2]},
            "target": {"x": x, "y": y, "z": z},
            "joint_positions": joint_positions
        }, None

    def calculate_joint_positions_3d(self, theta_base, theta_shoulder, theta_elbow):
        """Calcula posições 3D de todas as juntas do braço"""
        # Converter para radianos
        base_rad = np.radians(theta_base)
        shoulder_rad = np.radians(theta_shoulder)
        elbow_rad = np.radians(theta_elbow)

        # Posições das juntas em 3D
        # Base (origem)
        p0 = np.array([0.0, 0.0, 0.0])

        # Ombro
        p1 = np.array([
            self.ik_solver.l1 * np.cos(base_rad),
            self.ik_solver.l1 * np.sin(base_rad),
            0.0  # Base gira no plano XY
        ])

        # Cotovelo
        p2 = np.array([
            p1[0] + self.ik_solver.l2 * np.cos(base_rad + shoulder_rad),
            p1[1] + self.ik_solver.l2 * np.sin(base_rad + shoulder_rad),
            0.0  # Movimento planar
        ])

        # Ponta da garra
        p3 = np.array([
            p2[0] + self.ik_solver.l3 * np.cos(base_rad + shoulder_rad + elbow_rad),
            p2[1] + self.ik_solver.l3 * np.sin(base_rad + shoulder_rad + elbow_rad),
            0.0  # Movimento planar
        ])

        return [p0, p1, p2, p3]

    def get_workspace_bounds(self):
        """Retorna os limites aproximados do espaço de trabalho"""
        return {
            "x": (-0.25, 0.25),
            "y": (-0.25, 0.25),
            "z": (0.05, 0.30)
        }

    def close(self):
        """Fecha a visualização 3D"""
        if self.fig:
            try:
                import matplotlib.pyplot as plt
                plt.close(self.fig)
            except:
                pass

# Visualizador 2D sincronizado com coordenadas atuais
class SyncedArmVisualizer:
    def __init__(self, current_coords):
        self.current_coords = current_coords
        self.ik_solver = ArmInverseKinematics(link1_len=0.13, link2_len=0.11, link3_len=0.05)

        # Calcular ângulos iniciais
        angles = self.ik_solver.inverse_kinematics(
            current_coords['x'], current_coords['y'], current_coords['z']
        )
        if angles:
            self.theta_base, self.theta_shoulder, self.theta_elbow = angles
        else:
            self.theta_base, self.theta_shoulder, self.theta_elbow = 0, np.radians(90), np.radians(90)

        # Estado dos ângulos (em graus de servo calibrados)
        self.state = {
            "giro": float(np.degrees(self.theta_base)),
            "um": float(np.degrees(self.theta_shoulder)),
            "dois": float(np.degrees(self.theta_elbow)),
            "garra": 135,  # aberto
            "servo3": 33
        }

        # Aplicar calibração inicial
        self.state = self.apply_calibration_to_state(self.state)

    def apply_calibration_to_state(self, state):
        """Aplica calibração completa ao estado, igual ao sistema real"""
        calibrated = {}
        for k, v in state.items():
            try:
                val = float(v)
            except:
                calibrated[k] = v
                continue

            # Aplicar calibração (igual ao _apply_calibration_and_limits)
            import arm_pick_config as APC
            calib = APC.JOINT_CALIB.get(k, {})
            if calib.get("invert"):
                val = 180.0 - val
            val += float(calib.get("offset", 0.0))

            # Aplicar limites
            lim = APC.JOINT_LIMITS.get(k, (0, 180))
            val = float(np.clip(val, lim[0], lim[1]))

            calibrated[k] = int(round(val))
        return calibrated

    def run(self):
        """Executa o visualizador 2D sincronizado com controle real dos servos"""
        print("🎛️  Controles sincronizados (ENVIAM COMANDOS PARA OS SERVOS):")
        print("  r   -> reset para coordenadas atuais")
        print("  a/d -> um -/+ 2 deg (ombro)")
        print("  w/s -> dois -/+ 2 deg (cotovelo)")
        print("  q/e -> giro -/+ 2 deg (base)")
        print("  z/x -> garra -/+ 5 deg")
        print("  c   -> recalcular IK das coordenadas atuais")
        print("  m   -> enviar comando atual para os servos")
        print("  ESC -> sair")
        print("=" * 60)

        # Conectar aos servos
        try:
            from esp32_control import connect_esp32_garra, move_servos_esp32
            if not connect_esp32_garra():
                print("❌ Falha ao conectar ESP32. Modo visualização apenas.")
                servo_connected = False
            else:
                print("✅ ESP32 conectado. Comandos serão enviados aos servos.")
                servo_connected = True
        except ImportError:
            print("❌ Módulo esp32_control não encontrado. Modo visualização apenas.")
            servo_connected = False

        while True:
            img = np.zeros((600, 800, 3), dtype=np.uint8)
            self.draw_synced_scene(img, servo_connected)
            cv2.imshow("Visualizador 2D Sincronizado com Servo Control", img)
            key = cv2.waitKey(20) & 0xFF

            if key == 27:  # ESC
                break
            elif key in (ord('r'), ord('R')):
                # Reset para coordenadas atuais
                angles = self.ik_solver.inverse_kinematics(
                    self.current_coords['x'], self.current_coords['y'], self.current_coords['z']
                )
                if angles:
                    self.theta_base, self.theta_shoulder, self.theta_elbow = angles
                    self.state["giro"] = float(np.degrees(self.theta_base))
                    self.state["um"] = float(np.degrees(self.theta_shoulder))
                    self.state["dois"] = float(np.degrees(self.theta_elbow))
                    self.state = self.apply_calibration_to_state(self.state)
                    print("🔄 Reset para coordenadas atuais")
            elif key in (ord('c'), ord('C')):
                # Recalcular IK
                angles = self.ik_solver.inverse_kinematics(
                    self.current_coords['x'], self.current_coords['y'], self.current_coords['z']
                )
                if angles:
                    self.theta_base, self.theta_shoulder, self.theta_elbow = angles
                    self.state["giro"] = float(np.degrees(self.theta_base))
                    self.state["um"] = float(np.degrees(self.theta_shoulder))
                    self.state["dois"] = float(np.degrees(self.theta_elbow))
                    self.state = self.apply_calibration_to_state(self.state)
                    print("🔄 IK recalculado")
            elif key in (ord('m'), ord('M')):
                # Enviar comando atual para os servos
                if servo_connected:
                    try:
                        move_servos_esp32(self.state)
                        print(f"📡 Comando enviado: {self.state}")
                    except Exception as e:
                        print(f"❌ Erro ao enviar comando: {e}")
                else:
                    print("❌ ESP32 não conectado. Comando simulado.")
            elif key in (ord('a'), ord('A')):
                self.state["um"] -= 2
            elif key in (ord('d'), ord('D')):
                self.state["um"] += 2
            elif key in (ord('w'), ord('W')):
                self.state["dois"] -= 2
            elif key in (ord('s'), ord('S')):
                self.state["dois"] += 2
            elif key in (ord('q'), ord('Q')):
                self.state["giro"] -= 2
            elif key in (ord('e'), ord('E')):
                self.state["giro"] += 2
            elif key in (ord('z'), ord('Z')):
                self.state["garra"] -= 5
            elif key in (ord('x'), ord('X')):
                self.state["garra"] += 5

            # Aplicar calibração aos novos valores e manter limites
            for k in ["giro", "um", "dois", "garra", "servo3"]:
                self.state[k] = int(np.clip(self.state[k], 0, 180))

            # Reaplicar calibração após mudanças manuais
            self.state = self.apply_calibration_to_state(self.state)

    def draw_synced_scene(self, img, servo_connected):
        """Desenha a cena sincronizada"""
        cv2.rectangle(img, (0, 0), (799, 599), (40, 40, 40), 2)

        # Título
        title = "Visualizador 2D Sincronizado com Controle de Servo" if servo_connected else "Visualizador 2D (Modo Visualização)"
        cv2.putText(img, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Status da conexão
        status_color = (0, 255, 0) if servo_connected else (0, 0, 255)
        status_text = "🟢 SERVOS CONECTADOS - Comandos enviados em tempo real" if servo_connected else "🔴 MODO VISUALIZAÇÃO - Sem conexão com servos"
        cv2.putText(img, status_text, (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)

        # Coordenadas atuais
        cv2.putText(img, f"Coordenadas: X={self.current_coords['x']:.4f}, Y={self.current_coords['y']:.4f}, Z={self.current_coords['z']:.4f}",
                   (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Ângulos atuais
        cv2.putText(img, f"Angulos: giro={self.state['giro']:.1f}°, um={self.state['um']:.1f}°, dois={self.state['dois']:.1f}°, garra={self.state['garra']:.1f}°",
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Controles
        y = 70
        controls = [
            "r -> reset IK | a/d um -/+ | w/s dois -/+",
            "q/e giro -/+ | z/x garra -/+ | c recalcular IK",
            "m -> ENVIAR COMANDO PARA SERVOS | ESC sair"
        ]
        for control in controls:
            cv2.putText(img, control, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
            y += 18

        # Desenhar braço usando os ângulos atuais
        self.draw_arm_2d(img, self.state["um"], self.state["dois"])

    def draw_arm_2d(self, img, um_deg, dois_deg):
        """Desenha o braço 2D usando os ângulos atuais com calibração completa"""
        # Aplicar calibração completa como no sistema real
        import arm_pick_config as APC

        # Aplicar calibração e limites
        calib = APC.JOINT_CALIB.get("um", {})
        um_cal = um_deg
        if calib.get("invert", False):
            um_cal = 180.0 - um_cal
        um_cal += float(calib.get("offset", 0.0))

        calib = APC.JOINT_CALIB.get("dois", {})
        dois_cal = dois_deg
        if calib.get("invert", False):
            dois_cal = 180.0 - dois_cal
        dois_cal += float(calib.get("offset", 0.0))

        # Aplicar limites
        lim_um = APC.JOINT_LIMITS.get("um", (0, 180))
        lim_dois = APC.JOINT_LIMITS.get("dois", (0, 180))
        um_cal = float(np.clip(um_cal, lim_um[0], lim_um[1]))
        dois_cal = float(np.clip(dois_cal, lim_dois[0], lim_dois[1]))

        # Usar VIS_ZERO_DEG para mapeamento correto
        VIS_ZERO_DEG = getattr(APC, 'VIS_ZERO_DEG', {"um": 90.0, "dois": 90.0})
        th1 = np.radians(um_cal - VIS_ZERO_DEG.get("um", 90.0))
        th2 = np.radians(dois_cal - VIS_ZERO_DEG.get("dois", 90.0))

        # Comprimentos dos links
        L1, L2, L3 = 0.13, 0.11, 0.05
        SCALE = 800.0  # pixels per meter
        ORIGIN = (400, 500)  # base near bottom center

        # Posições das juntas
        x0, y0 = 0.0, 0.0
        x1 = x0 + L1 * np.cos(th1)
        y1 = y0 + L1 * np.sin(th1)
        x2 = x1 + L2 * np.cos(th1 + th2)
        y2 = y1 + L2 * np.sin(th1 + th2)
        x3 = x2 + L3 * np.cos(th1 + th2)
        y3 = y2 + L3 * np.sin(th1 + th2)

        # Converter para pixels
        def m2px(xm, ym):
            return (int(ORIGIN[0] + xm * SCALE), int(ORIGIN[1] - ym * SCALE))

        p0 = m2px(x0, y0)
        p1 = m2px(x1, y1)
        p2 = m2px(x2, y2)
        p3 = m2px(x3, y3)

        # Desenhar links
        cv2.circle(img, p0, 8, (200, 200, 200), -1)  # Base
        cv2.line(img, p0, p1, (255, 120, 0), 6)      # Link 1
        cv2.circle(img, p1, 6, (255, 255, 255), -1)  # Ombro
        cv2.line(img, p1, p2, (0, 200, 255), 6)      # Link 2
        cv2.circle(img, p2, 6, (255, 255, 255), -1)  # Cotovelo
        cv2.line(img, p2, p3, (0, 255, 120), 4)      # Link 3
        cv2.circle(img, p3, 8, (0, 255, 0), -1)      # Garra

        # Posição alvo (calculada das coordenadas atuais)
        target_px = m2px(self.current_coords['x'], self.current_coords['z'])
        cv2.drawMarker(img, target_px, (0, 255, 255), cv2.MARKER_STAR, 20, 2)

        # Mostrar informações de calibração
        y_info = 550
        cv2.putText(img, f"um: {um_deg:.1f}° -> cal: {um_cal:.1f}°", (10, y_info),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_info -= 15
        cv2.putText(img, f"dois: {dois_deg:.1f}° -> cal: {dois_cal:.1f}°", (10, y_info),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_info -= 15

        # Avisos de clamp
        if abs(um_cal - um_deg) > 0.1:
            cv2.putText(img, f"⚠️ um clamped: {um_deg:.1f} -> {um_cal:.1f}", (10, y_info),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            y_info -= 15
        if abs(dois_cal - dois_deg) > 0.1:
            cv2.putText(img, f"⚠️ dois clamped: {dois_deg:.1f} -> {dois_cal:.1f}", (10, y_info),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            y_info -= 15

        # Mostrar comando que seria enviado aos servos
        servo_cmd = f"Servo cmd: giro={self.state['giro']}, um={self.state['um']}, dois={self.state['dois']}, garra={self.state['garra']}"
        cv2.putText(img, servo_cmd, (10, y_info), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
        y_info -= 15

        # Calcular e mostrar coordenadas XYZ da posição atual
        try:
            # Ângulos em radianos para FK
            theta_base_rad = np.radians(self.state['giro'])
            theta_shoulder_rad = np.radians(self.state['um'])
            theta_elbow_rad = np.radians(self.state['dois'])

            # Forward kinematics
            x_fk = (0.13 * np.cos(theta_base_rad) +
                   0.11 * np.cos(theta_base_rad + theta_shoulder_rad) +
                   0.05 * np.cos(theta_base_rad + theta_shoulder_rad + theta_elbow_rad))

            y_fk = (0.13 * np.sin(theta_base_rad) +
                   0.11 * np.sin(theta_base_rad + theta_shoulder_rad) +
                   0.05 * np.sin(theta_base_rad + theta_shoulder_rad + theta_elbow_rad))

            z_fk = 0.0  # Movimento planar

            xyz_text = f"Posição XYZ: X={x_fk:.4f}, Y={y_fk:.4f}, Z={z_fk:.4f}"
            cv2.putText(img, xyz_text, (10, y_info), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        except Exception as e:
            cv2.putText(img, f"Erro cálculo XYZ: {str(e)}", (10, y_info), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

# Menu interativo para calibração virtual 3D
def interactive_virtual_calibration_menu():
    simulator = VirtualArmSimulator3D()
    virtual_coords = {"x": 0.0, "y": 0.08, "z": 0.10}

    print("🤖 Simulador Virtual 3D do Braço Robótico")
    print("=" * 60)
    print("Use este modo para visualizar e encontrar coordenadas seguras")
    print("antes de mover o braço real. Requer matplotlib instalado.")
    print("=" * 60)

    while True:
        print(f"\n📍 Posição atual: X={virtual_coords['x']:.4f}, Y={virtual_coords['y']:.4f}, Z={virtual_coords['z']:.4f}")
        print("\n🎛️  Menu de Calibração Virtual:")
        print("1. Simular posição atual")
        print("2. Ajustar coordenada X")
        print("3. Ajustar coordenada Y")
        print("4. Ajustar coordenada Z")
        print("5. Mostrar limites do espaço de trabalho")
        print("6. Aplicar coordenadas no braço real")
        print("7. Sair")
        print("=" * 40)

        try:
            choice = input("Escolha uma opção (1-7): ").strip()

            if choice == "1":
                result, error = simulator.simulate_position(
                    virtual_coords['x'], virtual_coords['y'], virtual_coords['z']
                )
                if error:
                    print(f"❌ {error}")
                else:
                    print("✅ Simulação bem-sucedida:")
                    print(f"   Ângulos: giro={result['angles']['giro']:.2f}°, um={result['angles']['um']:.2f}°, dois={result['angles']['dois']:.2f}°")
                    print(f"   Posição FK: X={result['position']['x']:.4f}, Y={result['position']['y']:.4f}, Z={result['position']['z']:.4f}")
                    print(f"   Alvo: X={result['target']['x']:.4f}, Y={result['target']['y']:.4f}, Z={result['target']['z']:.4f}")

            elif choice == "2":
                bounds = simulator.get_workspace_bounds()
                new_x = float(input(f"Digite nova coordenada X ({bounds['x'][0]:.3f} a {bounds['x'][1]:.3f}): "))
                if bounds['x'][0] <= new_x <= bounds['x'][1]:
                    virtual_coords["x"] = new_x
                    print(f"✅ X atualizado para {virtual_coords['x']:.4f}")
                else:
                    print(f"❌ X fora dos limites: {bounds['x'][0]:.3f} a {bounds['x'][1]:.3f}")

            elif choice == "3":
                bounds = simulator.get_workspace_bounds()
                new_y = float(input(f"Digite nova coordenada Y ({bounds['y'][0]:.3f} a {bounds['y'][1]:.3f}): "))
                if bounds['y'][0] <= new_y <= bounds['y'][1]:
                    virtual_coords["y"] = new_y
                    print(f"✅ Y atualizado para {virtual_coords['y']:.4f}")
                else:
                    print(f"❌ Y fora dos limites: {bounds['y'][0]:.3f} a {bounds['y'][1]:.3f}")

            elif choice == "4":
                bounds = simulator.get_workspace_bounds()
                new_z = float(input(f"Digite nova coordenada Z ({bounds['z'][0]:.3f} a {bounds['z'][1]:.3f}): "))
                if bounds['z'][0] <= new_z <= bounds['z'][1]:
                    virtual_coords["z"] = new_z
                    print(f"✅ Z atualizado para {virtual_coords['z']:.4f}")
                else:
                    print(f"❌ Z fora dos limites: {bounds['z'][0]:.3f} a {bounds['z'][1]:.3f}")

            elif choice == "5":
                bounds = simulator.get_workspace_bounds()
                print("🏗️  Limites do espaço de trabalho:")
                print(f"   X: {bounds['x'][0]:.3f} a {bounds['x'][1]:.3f} m")
                print(f"   Y: {bounds['y'][0]:.3f} a {bounds['y'][1]:.3f} m")
                print(f"   Z: {bounds['z'][0]:.3f} a {bounds['z'][1]:.3f} m")

            elif choice == "6":
                print("⚠️  Aplicando coordenadas no braço real...")
                print(f"Coordenadas: X={virtual_coords['x']:.4f}, Y={virtual_coords['y']:.4f}, Z={virtual_coords['z']:.4f}")

                # Salvar para o modo real
                try:
                    with open('manual_coords.txt', 'w') as f:
                        f.write(f"{virtual_coords['x']},{virtual_coords['y']},{virtual_coords['z']}")
                    print("💾 Coordenadas salvas para o modo real")
                except:
                    print("⚠️  Não foi possível salvar coordenadas")

                confirm = input("Deseja testar no braço real agora? (s/n): ").lower().strip()
                if confirm == 's':
                    return virtual_coords
                else:
                    print("Coordenadas salvas. Use o menu principal para testar.")

            elif choice == "7":
                print("Saindo do simulador...")
                simulator.close()
                return None
            else:
                print("Opção inválida. Tente novamente.")

        except ValueError:
            print("Entrada inválida. Digite um número.")
        except KeyboardInterrupt:
            print("\nSaindo do simulador...")
            return None

# Remover toda a segunda definição da classe DynamicArmController

# Menu principal com simulador virtual
if __name__ == "__main__":
    print("🚀 Sistema de Controle da Garra Robótica")
    print("=" * 50)

    while True:
        print("\n🎛️  Menu Principal:")
        print("1. Simulador Virtual 3D (Calibração Segura)")
        print("2. Visualizador 2D (OpenCV)")
        print("3. Modo Manual (Braço Real)")
        print("4. Modo Automático (AprilTags)")
        print("5. Sair")
        print("=" * 40)

        try:
            choice = input("Escolha uma opção (1-5): ").strip()

            if choice == "1":
                print("\n🤖 Entrando no Simulador Virtual 3D...")
                result = interactive_virtual_calibration_menu()
                if result:
                    print(f"\n✅ Coordenadas aplicadas: X={result['x']:.4f}, Y={result['y']:.4f}, Z={result['z']:.4f}")
                    print("Agora você pode usar o Modo Manual para testar no braço real")

            elif choice == "2":
                print("\n📺 Entrando no Visualizador 2D Sincronizado...")
                try:
                    # Carregar coordenadas atuais
                    manual_coords = {"x": -0.02, "y": 0.08, "z": 0.10}
                    try:
                        with open('manual_coords.txt', 'r') as f:
                            data = f.read().strip().split(',')
                            manual_coords = {
                                "x": float(data[0]),
                                "y": float(data[1]),
                                "z": float(data[2])
                            }
                    except:
                        pass

                    # Calcular ângulos IK para as coordenadas atuais
                    ik_solver = ArmInverseKinematics(link1_len=0.13, link2_len=0.11, link3_len=0.05)
                    angles = ik_solver.inverse_kinematics(
                        manual_coords['x'], manual_coords['y'], manual_coords['z']
                    )

                    if angles:
                        theta_base, theta_shoulder, theta_elbow = angles
                        print(f"🔧 Coordenadas atuais: X={manual_coords['x']:.4f}, Y={manual_coords['y']:.4f}, Z={manual_coords['z']:.4f}")
                        print(f"🔧 Ângulos calculados: giro={theta_base:.2f}°, um={theta_shoulder:.2f}°, dois={theta_elbow:.2f}°")
                        print("📺 Iniciando visualizador 2D sincronizado...")

                        # Criar visualizador sincronizado
                        synced_visualizer = SyncedArmVisualizer(manual_coords)
                        synced_visualizer.run()
                    else:
                        print("❌ Não foi possível calcular ângulos para as coordenadas atuais")

                except Exception as e:
                    print(f"❌ Erro ao executar visualizador sincronizado: {e}")
                    import traceback
                    traceback.print_exc()

            elif choice == "3":
                # Carregar coordenadas salvas se existirem
                manual_coords = {"x": -0.02, "y": 0.08, "z": 0.10}
                try:
                    with open('manual_coords.txt', 'r') as f:
                        data = f.read().strip().split(',')
                        manual_coords = {
                            "x": float(data[0]),
                            "y": float(data[1]),
                            "z": float(data[2])
                        }
                    print(f"📁 Coordenadas carregadas: X={manual_coords['x']:.4f}, Y={manual_coords['y']:.4f}, Z={manual_coords['z']:.4f}")
                except:
                    print("📝 Usando coordenadas padrão")

                # Menu de calibração manual
                def interactive_calibration_menu():
                    while True:
                        print(f"\n📍 Coordenadas atuais: X={manual_coords['x']:.4f}, Y={manual_coords['y']:.4f}, Z={manual_coords['z']:.4f}")
                        print("\n🎛️  Menu de Calibração Manual:")
                        print("1. Testar coordenadas atuais")
                        print("2. Ajustar coordenada X")
                        print("3. Ajustar coordenada Y")
                        print("4. Ajustar coordenada Z")
                        print("5. Executar teste completo (AprilTags)")
                        print("6. Voltar ao menu principal")
                        print("=" * 40)

                        try:
                            sub_choice = input("Escolha uma opção (1-6): ").strip()

                            if sub_choice == "1":
                                return "test_current"
                            elif sub_choice == "2":
                                try:
                                    new_x = float(input(f"X atual: {manual_coords['x']:.4f}. Novo X: "))
                                    manual_coords["x"] = new_x
                                    print(f"✅ X atualizado para {manual_coords['x']:.4f}")
                                except ValueError:
                                    print("❌ Valor inválido")
                            elif sub_choice == "3":
                                try:
                                    new_y = float(input(f"Y atual: {manual_coords['y']:.4f}. Novo Y: "))
                                    manual_coords["y"] = new_y
                                    print(f"✅ Y atualizado para {manual_coords['y']:.4f}")
                                except ValueError:
                                    print("❌ Valor inválido")
                            elif sub_choice == "4":
                                try:
                                    new_z = float(input(f"Z atual: {manual_coords['z']:.4f}. Novo Z: "))
                                    manual_coords["z"] = new_z
                                    print(f"✅ Z atualizado para {manual_coords['z']:.4f}")
                                except ValueError:
                                    print("❌ Valor inválido")
                            elif sub_choice == "5":
                                return "run_full_test"
                            elif sub_choice == "6":
                                return "exit"
                            else:
                                print("Opção inválida.")
                        except KeyboardInterrupt:
                            return "exit"

                action = interactive_calibration_menu()

                if action == "exit":
                    break
                elif action == "test_current":
                    print(f"Testando coordenadas: X={manual_coords['x']:.4f}, Y={manual_coords['y']:.4f}, Z={manual_coords['z']:.4f}")
                    controller = DynamicArmController(target_tag_ids=[10], manual_mode=True, manual_coords=manual_coords)
                    try:
                        success = controller.run_manual_test()
                        if success:
                            print("✅ Teste concluído com sucesso")
                        else:
                            print("❌ Teste falhou")
                        input("Pressione Enter para continuar...")
                    finally:
                        controller.close()
                elif action.startswith("set_x_"):
                    new_x = float(action.split("_")[2])
                    manual_coords["x"] = new_x
                    print(f"✅ X atualizado para {manual_coords['x']:.4f}")
                elif action.startswith("set_y_"):
                    new_y = float(action.split("_")[2])
                    manual_coords["y"] = new_y
                    print(f"✅ Y atualizado para {manual_coords['y']:.4f}")
                elif action.startswith("set_z_"):
                    new_z = float(action.split("_")[2])
                    manual_coords["z"] = new_z
                    print(f"✅ Z atualizado para {manual_coords['z']:.4f}")
                elif action == "run_full_test":
                    # Criar controller sem modo manual para usar run_cycle
                    controller = DynamicArmController(target_tag_ids=[10])
                    try:
                        while True:
                            detected_count = controller.run_cycle()
                            if detected_count > 0:
                                print(f"✅ {detected_count} tags processadas neste ciclo")
                            else:
                                print("⏳ Nenhuma tag alvo detectada")

                            time.sleep(5)

                    except KeyboardInterrupt:
                        print("\n⏹️ Interrompido pelo usuário")
                    finally:
                        controller.close()
                    break
                elif action.startswith("set_x_"):
                    new_x = float(action.split("_")[2])
                    manual_coords["x"] = new_x
                    print(f"✅ X atualizado para {manual_coords['x']:.4f}")
                elif action.startswith("set_y_"):
                    new_y = float(action.split("_")[2])
                    manual_coords["y"] = new_y
                    print(f"✅ Y atualizado para {manual_coords['y']:.4f}")
                elif action.startswith("set_z_"):
                    new_z = float(action.split("_")[2])
                    manual_coords["z"] = new_z
                    print(f"✅ Z atualizado para {manual_coords['z']:.4f}")
                elif action == "run_full_test":
                    controller = DynamicArmController(target_tag_ids=[10])
                    try:
                        while True:
                            detected_count = controller.run_cycle()
                            if detected_count > 0:
                                print(f"✅ {detected_count} tags processadas neste ciclo")
                            else:
                                print("⏳ Nenhuma tag alvo detectada")

                            time.sleep(5)

                    except KeyboardInterrupt:
                        print("\n⏹️ Interrompido pelo usuário")
                    finally:
                        controller.close()
                    break

            elif choice == "4":
                print("\n🎯 Entrando no Modo Automático com AprilTags...")
                # Usar a primeira classe DynamicArmController que tem run_cycle
                controller = DynamicArmController(target_tag_ids=[10])
                try:
                    while True:
                        detected_count = controller.run_cycle()
                        if detected_count > 0:
                            print(f"✅ {detected_count} tags processadas neste ciclo")
                        else:
                            print("⏳ Nenhuma tag alvo detectada")

                        time.sleep(5)

                except KeyboardInterrupt:
                    print("\n⏹️ Interrompido pelo usuário")
                finally:
                    controller.close()

            elif choice == "5":
                print("👋 Saindo do sistema...")
                break
            else:
                print("Opção inválida. Tente novamente.")

        except ValueError:
            print("Entrada inválida. Digite um número.")
        except KeyboardInterrupt:
            print("\n👋 Saindo do sistema...")
            break