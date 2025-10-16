#!/usr/bin/env python3
"""
Navegação Básica do AGV
Movimento em linha reta + curvas de 90 graus usando MPU6050
"""

import time
import math
import os
import cv2
from datetime import datetime
from mpu6050_integration import MPU6050Integration
from config import get_esp32_port, get_esp32_baudrate, NAVIGATION_CONFIG, HARDWARE_CONFIG
from line_detector import LineDetector, PICAMERA2_AVAILABLE

class BasicNavigation:
    """Navegação básica: linha reta + curvas de 90°"""

    def __init__(self, esp32_port=None):
        self.mpu = MPU6050Integration(esp32_port=esp32_port or get_esp32_port(), baudrate=get_esp32_baudrate())
        self.velocidade_base = 80  # Velocidade padrão (0-100)

        # Configurações de navegação
        self.angulo_curva = 90  # Graus para curvas
        self.tolerancia_angulo = 5  # Tolerância em graus
        self.distancia_minima = 50  # cm (simulado)

        # Estado atual
        self.posicao_atual = {'x': 0, 'y': 0, 'angulo': 0}
        self.movimento_ativo = False
        # Detector de linha compartilhado (para evitar múltiplas instâncias de Picamera2)
        self.shared_detector = None
        # Pasta de snapshots para depuração
        self.snapshots_dir = os.path.join(os.path.dirname(__file__), 'captures')

    def set_shared_detector(self, detector):
        """Opcional: usar um LineDetector compartilhado vindo de níveis superiores.
        Isso evita múltiplas instâncias de Picamera2 e previne erros de estado.
        """
        self.shared_detector = detector

    def inicializar(self):
        """Inicializar navegação"""
        print("INICIALIZANDO NAVEGACAO BASICA")
        print("=" * 40)

        if not self.mpu.conectar_esp32():
            print("Erro ao conectar ESP32: module 'serial' has no attribute 'Serial'")
            return False

        if not self.mpu.calibrar_sensor():
            print("❌ Falha na calibração do MPU6050")
            return False

        print("✅ Navegação inicializada!")
        return True

    def mover_em_linha_reta(self, distancia_cm, direcao='frente'):
        """Mover em linha reta por uma distância"""
        try:
            print(f"📏 Movendo em linha reta: {distancia_cm}cm para {direcao}")

            # Calcular tempo baseado na velocidade (simulação)
            # Velocidade aproximada: 20 cm/s
            tempo_movimento = distancia_cm / 20.0

            # Enviar comando de movimento
            if direcao == 'frente':
                self.mpu.enviar_comando('mover_frente', {'velocidade': self.velocidade_base})
            else:
                self.mpu.enviar_comando('mover_tras', {'velocidade': self.velocidade_base})

            # Monitorar movimento
            inicio = time.time()
            while time.time() - inicio < tempo_movimento:
                status = self.mpu.obter_status_completo()

                if status:
                    # Mostrar progresso
                    progresso = (time.time() - inicio) / tempo_movimento * 100
                    print(f"Progresso: {progresso:.1f}%")
                time.sleep(0.1)

            # Parar movimento
            self.parar()

            # Atualizar posição (simulação)
            angulo_rad = math.radians(self.posicao_atual['angulo'])
            delta_x = distancia_cm * math.cos(angulo_rad) if direcao == 'frente' else -distancia_cm * math.cos(angulo_rad)
            delta_y = distancia_cm * math.sin(angulo_rad) if direcao == 'frente' else -distancia_cm * math.sin(angulo_rad)

            self.posicao_atual['x'] += delta_x
            self.posicao_atual['y'] += delta_y

            print(f"Posição atualizada: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}")
            return True
        except Exception as e:
            print(f"❌ Erro no movimento em linha reta: {e}")
            self.parar()
            return False

    def parar(self):
        """Parar todos os movimentos"""
        try:
            # Somente enviar comando se houver conexão serial ativa
            if getattr(self.mpu, 'serial_conn', None):
                self.mpu.enviar_comando('parar')
            else:
                print("(simulação) parar")
            self.movimento_ativo = False
            print("🛑 Movimento parado")
            return True
        except Exception as e:
            print(f"❌ Erro ao parar: {e}")
            return False

    def virar_90_graus(self, direcao='direita'):
        """Fazer curva de 90 graus baseada em ângulo do MPU6050 com controle melhorado"""
        try:
            print(f"🔄 Virando 90° para a {direcao}")

            # Parâmetros de giro do config
            turn_cfg = NAVIGATION_CONFIG.get('turn', {}) if isinstance(NAVIGATION_CONFIG, dict) else {}
            strategy = str(turn_cfg.get('strategy', 'gyro'))
            simple_mode = bool(turn_cfg.get('simple_mode', False))
            slow_simple = float(turn_cfg.get('slowdown_start_deg', 10.0))
            v_max = int(turn_cfg.get('max_speed', 28))
            v_min = int(turn_cfg.get('min_speed', 6))
            th_slow = float(turn_cfg.get('slowdown_threshold_deg', 18.0))
            tol_stop = float(turn_cfg.get('stop_tolerance_deg', 0.8))
            base_comp = float(turn_cfg.get('inertia_comp_deg', 2.0))
            k_rate = float(turn_cfg.get('inertia_rate_k', 0.03))
            k_speed = float(turn_cfg.get('speed_k', 1.0))
            pause_after = float(turn_cfg.get('brake_pause_s', 0.4))
            slowdown_gamma = float(turn_cfg.get('slowdown_gamma', 1.0))
            sign_flip_brake = bool(turn_cfg.get('sign_flip_brake', False))
            dynamic_comp = bool(turn_cfg.get('dynamic_compensation', False))

            # Comando base para o motor conforme direção solicitada
            comando = 'virar_direita' if direcao == 'direita' else 'virar_esquerda'
            # Aplicar inversão global se configurada
            try:
                inv_cfg = bool(NAVIGATION_CONFIG.get('turn', {}).get('invert_commands', False)) or bool(HARDWARE_CONFIG.get('motors', {}).get('invert_turn_commands', False))
            except Exception:
                inv_cfg = False
            if inv_cfg:
                comando = 'virar_esquerda' if comando == 'virar_direita' else 'virar_direita'

            # Modo exclusivamente por visão: não usa giroscópio (sem pré-giro, sem leitura de ângulo)
            if strategy == 'vision_center' and PICAMERA2_AVAILABLE:
                vis = turn_cfg.get('vision', {}) if isinstance(turn_cfg, dict) else {}
                exclusive = bool(vis.get('exclusive', False))
                if exclusive:
                    tol_px = float(vis.get('tolerance_px', 22))
                    slow_px = float(vis.get('slowdown_px', 110))
                    min_conf = float(vis.get('min_confidence', 0.45))
                    v_fast = int(vis.get('speed_fast', v_max))
                    v_slow = int(vis.get('speed_slow', max(v_min, 8)))
                    v_fast = max(v_min, min(v_max, v_fast))
                    v_slow = max(v_min, min(v_max, v_slow))
                    timeout_vis = float(vis.get('timeout_s', 8.0))
                    target_offset = float(vis.get('target_offset_px', 0.0))

                    # Usar detector compartilhado se disponível para evitar conflito de câmera
                    detector = self.shared_detector if self.shared_detector is not None else LineDetector()
                    needs_init = getattr(detector, 'picam2', None) is None
                    if needs_init:
                        if not detector.initialize():
                            print("❌ Falha ao iniciar câmera para curva por visão (exclusiva)")
                            return False

                    print("👁️ Curva por visão (exclusiva): girar até a linha centralizar")
                    # Iniciar captura contínua para estabilidade
                    started_cont = False
                    try:
                        started_cont = detector.start_continuous_capture()
                    except Exception as e:
                        print(f"⚠️ Falha ao iniciar captura contínua: {e}")

                    t0 = time.time()
                    last_speed = None
                    last_snap = 0.0
                    # Começar com velocidade rápida para iniciar a curva
                    if getattr(self.mpu, 'serial_conn', None):
                        self.mpu.enviar_comando(comando, {'velocidade': v_fast})

                    while time.time() - t0 < timeout_vis:
                        frame = None
                        try:
                            frame = detector.capture_continuous_frame()
                        except Exception:
                            frame = None
                        info = detector.process_frame(frame) if frame is not None else None
                        if info and info.get('detected') and info.get('confidence', 0) >= min_conf:
                            img_center = detector.width // 2
                            err_raw = int(info.get('center', img_center)) - img_center
                            desired = -target_offset if direcao == 'direita' else target_offset
                            err = err_raw - desired
                            abs_err = abs(err)
                            print(f"Visão: err_raw={err_raw}, alvo={desired}, erro_px={err}, conf={info.get('confidence',0):.2f}")
                            # Snapshots periódicos
                            if time.time() - last_snap > 0.3:
                                try:
                                    visf = info.get('frame_bgr')
                                    if visf is not None:
                                        img = visf.copy()
                                        cv2.rectangle(img, (0, detector.roi_y_start),
                                                      (detector.width, detector.roi_y_start + detector.roi_height),
                                                      (255, 0, 0), 1)
                                        cv2.line(img, (detector.width // 2, detector.roi_y_start),
                                                 (detector.width // 2, detector.roi_y_start + detector.roi_height),
                                                 (0, 255, 255), 1)
                                        cx = int(info.get('center', img_center))
                                        cy = detector.roi_y_start + detector.roi_height // 2
                                        cv2.circle(img, (cx, cy), 5, (0, 255, 0), -1)
                                        cv2.putText(img, f"err={err} px conf={info.get('confidence',0):.2f}",
                                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                                        os.makedirs(self.snapshots_dir, exist_ok=True)
                                        cv2.imwrite(os.path.join(self.snapshots_dir, f"vision_turn_{int(time.time()*1000)}.png"), img)
                                except Exception:
                                    pass
                                last_snap = time.time()
                            if abs_err <= tol_px:
                                print(f"✅ Linha centralizada (|erro|={abs_err}px <= {tol_px}px)")
                                self.parar()
                                time.sleep(pause_after)
                                try:
                                    if started_cont:
                                        detector.stop_continuous_capture()
                                except Exception:
                                    pass
                                return True
                            speed_cmd = v_slow if abs_err <= slow_px else v_fast
                            if speed_cmd != last_speed:
                                self.mpu.enviar_comando(comando, {'velocidade': speed_cmd})
                                last_speed = speed_cmd
                        else:
                            # Sem linha confiável: gira devagar enquanto procura
                            if last_speed != v_slow:
                                self.mpu.enviar_comando(comando, {'velocidade': v_slow})
                                last_speed = v_slow
                        time.sleep(0.06)

                    print("⏱️ Timeout visão sem centralizar; parando")
                    self.parar()
                    time.sleep(pause_after)
                    try:
                        if started_cont:
                            detector.stop_continuous_capture()
                    except Exception:
                        pass
                    return False

            # Obter ângulo inicial
            angulo_inicial = self.get_current_angle()
            if angulo_inicial is None:
                print("❌ Não foi possível obter ângulo inicial")
                return False

            # Determinar direção da curva (convenção corrigida):
            # Direita diminui ângulo (-), Esquerda aumenta ângulo (+)
            sentido = -1 if direcao == 'direita' else 1

            # Ângulo alvo
            angulo_alvo = angulo_inicial + (self.angulo_curva * sentido)

            # Normalizar ângulo alvo (0-360)
            angulo_alvo = angulo_alvo % 360

            # Compensação base de inércia; ajustaremos dinamicamente com taxa
            compensacao_inercia = base_comp
            angulo_parada = angulo_alvo - (compensacao_inercia * sentido)
            angulo_parada = angulo_parada % 360

            print(f"Ângulo inicial: {angulo_inicial:.1f}°")
            print(f"Ângulo alvo: {angulo_alvo:.1f}°")
            print(f"Ângulo de parada: {angulo_parada:.1f}° (compensação: {compensacao_inercia:.1f}°)")
            print(f"Estratégia de curva: {strategy}")

            # Selecionar comando base conforme direção solicitada
            comando = 'virar_direita' if direcao == 'direita' else 'virar_esquerda'
            # Aplicar inversão global se configurada
            try:
                inv_cfg = bool(NAVIGATION_CONFIG.get('turn', {}).get('invert_commands', False)) or bool(HARDWARE_CONFIG.get('motors', {}).get('invert_turn_commands', False))
            except Exception:
                inv_cfg = False
            if inv_cfg:
                comando = 'virar_esquerda' if comando == 'virar_direita' else 'virar_direita'

            # Auto-teste curto baseado no sinal do yaw: direita deve diminuir, esquerda deve aumentar
            if getattr(self.mpu, 'serial_conn', None):
                test_speed = max(v_min, int(0.6 * v_max))
                test_pulse = 0.08
                ang0 = angulo_inicial
                self.mpu.enviar_comando(comando, {'velocidade': test_speed})
                time.sleep(test_pulse)
                self.parar()
                ang1 = self.get_current_angle()
                if ang1 is not None:
                    dyaw = self.calcular_diferenca_angular(ang0, ang1)
                    print(f"🔎 Probe yaw Δ={dyaw:.2f}° (direção esperada: {'-' if direcao=='direita' else '+'})")
                    # Direita => dyaw deve ser negativo; Esquerda => dyaw deve ser positivo
                    if (direcao == 'direita' and dyaw > 0) or (direcao == 'esquerda' and dyaw < 0):
                        comando = 'virar_esquerda' if comando == 'virar_direita' else 'virar_direita'
                        sentido = -sentido
                        angulo_inicial = ang1
                        angulo_alvo = (angulo_inicial + (self.angulo_curva * sentido)) % 360
                        compensacao_inercia = base_comp
                        angulo_parada = (angulo_alvo - (compensacao_inercia * sentido)) % 360
                        print(f"🔁 Auto-ajuste de direção (yaw): invertido | novo alvo: {angulo_alvo:.1f}°, novo parada: {angulo_parada:.1f}°")

            # Estratégia: Visão - parar quando a linha estiver centralizada na câmera
            if strategy == 'vision_center' and PICAMERA2_AVAILABLE:
                vis = turn_cfg.get('vision', {}) if isinstance(turn_cfg, dict) else {}
                tol_px = float(vis.get('tolerance_px', 22))
                slow_px = float(vis.get('slowdown_px', 110))
                min_conf = float(vis.get('min_confidence', 0.45))
                v_fast = int(vis.get('speed_fast', v_max))
                v_slow = int(vis.get('speed_slow', max(v_min, 8)))
                v_fast = max(v_min, min(v_max, v_fast))
                v_slow = max(v_min, min(v_max, v_slow))
                timeout_vis = float(vis.get('timeout_s', 8.0))
                target_offset = float(vis.get('target_offset_px', 0.0))
                start_delay = float(vis.get('start_delay_s', 0.0))
                start_prog = float(vis.get('start_progress_deg', 0.0))

                # Primeiro, faça um giro inicial (gyro) para sair da interseção
                if start_delay > 0 or start_prog > 0:
                    print(f"⏳ Giro inicial antes da visão: delay={start_delay:.2f}s, progresso={start_prog:.1f}°")
                    ang0 = self.get_current_angle()
                    t_start = time.time()
                    self.mpu.enviar_comando(comando, {'velocidade': v_fast})
                    while True:
                        time.sleep(0.05)
                        if start_delay and (time.time() - t_start) >= start_delay:
                            break
                        if start_prog and ang0 is not None:
                            ang_now = self.get_current_angle()
                            if ang_now is not None:
                                prog_now = abs(self.calcular_diferenca_angular(ang0, ang_now))
                                if prog_now >= start_prog:
                                    break
                    self.parar()
                    time.sleep(0.05)

                # Usar detector compartilhado se disponível para evitar conflito de câmera
                detector = self.shared_detector if self.shared_detector is not None else LineDetector()
                needs_init = getattr(detector, 'picam2', None) is None
                if needs_init:
                    if not detector.initialize():
                        print("⚠️ Falha ao iniciar visão; usando fallback giroscópio")
                        detector = None
                if detector is None:
                    pass
                else:
                    print("👁️ Curva por visão: parar quando a linha centralizar")
                    # Iniciar captura contínua para evitar start/stop repetidos
                    started_cont = False
                    try:
                        started_cont = detector.start_continuous_capture()
                    except Exception as e:
                        print(f"⚠️ Falha ao iniciar captura contínua: {e}")
                    t0 = time.time()
                    last_speed = None
                    last_snap = 0.0
                    while time.time() - t0 < timeout_vis:
                        # Obter frame atual da sessão contínua
                        frame = None
                        try:
                            frame = detector.capture_continuous_frame()
                        except Exception:
                            frame = None
                        info = detector.process_frame(frame) if frame is not None else None
                        if info and info.get('detected') and info.get('confidence', 0) >= min_conf:
                            img_center = detector.width // 2
                            err_raw = int(info.get('center', img_center)) - img_center
                            # Aplicar desvio alvo: para direita queremos parar um pouco antes (offset negativo), esquerda positivo
                            desired = -target_offset if direcao == 'direita' else target_offset
                            err = err_raw - desired
                            abs_err = abs(err)
                            print(f"Visão: err_raw={err_raw}, alvo={desired}, erro_px={err}, conf={info.get('confidence',0):.2f}")
                            # Snapshot de depuração (com overlays) a cada ~0.3s
                            if time.time() - last_snap > 0.3:
                                try:
                                    vis = info.get('frame_bgr')
                                    if vis is not None:
                                        vis = vis.copy()
                                        # Desenhar ROI
                                        cv2.rectangle(vis, (0, detector.roi_y_start),
                                                      (detector.width, detector.roi_y_start + detector.roi_height),
                                                      (255, 0, 0), 1)
                                        # Linha central e centro detectado
                                        cv2.line(vis, (detector.width // 2, detector.roi_y_start),
                                                 (detector.width // 2, detector.roi_y_start + detector.roi_height),
                                                 (0, 255, 255), 1)
                                        cx = int(info.get('center', img_center))
                                        cy = detector.roi_y_start + detector.roi_height // 2
                                        cv2.circle(vis, (cx, cy), 5, (0, 255, 0), -1)
                                        # Texto de erro
                                        cv2.putText(vis, f"err={err} px conf={info.get('confidence',0):.2f}",
                                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                                        # Garantir pasta
                                        os.makedirs(self.snapshots_dir, exist_ok=True)
                                        fname = os.path.join(self.snapshots_dir, f"vision_turn_{int(time.time()*1000)}.png")
                                        cv2.imwrite(fname, vis)
                                except Exception as _e:
                                    pass
                                last_snap = time.time()
                            if abs_err <= tol_px:
                                print(f"✅ Linha centralizada (|erro|={abs_err}px <= {tol_px}px)")
                                self.parar()
                                time.sleep(pause_after)
                                angulo_final = self.get_current_angle()
                                if angulo_final is not None:
                                    self.posicao_atual['angulo'] = angulo_final
                                    print(f"Ângulo final (visão): {angulo_final:.1f}°")
                                # Parar captura contínua
                                try:
                                    if started_cont:
                                        detector.stop_continuous_capture()
                                except Exception:
                                    pass
                                return True
                            speed_cmd = v_slow if abs_err <= slow_px else v_fast
                            if speed_cmd != last_speed:
                                self.mpu.enviar_comando(comando, {'velocidade': speed_cmd})
                                last_speed = speed_cmd
                        else:
                            # Sem linha confiável: gira devagar e continue procurando
                            if last_speed != v_slow:
                                self.mpu.enviar_comando(comando, {'velocidade': v_slow})
                                last_speed = v_slow
                        time.sleep(0.06)
                    print("⏱️ Timeout visão sem centralizar; parando")
                    self.parar()
                    time.sleep(pause_after)
                    # Parar captura contínua ao sair
                    try:
                        if detector and started_cont:
                            detector.stop_continuous_capture()
                    except Exception:
                        pass
                    return False

            # Estratégia: Tempo - girar por uma duração fixa
            if strategy == 'time':
                tcfg = turn_cfg.get('time', {}) if isinstance(turn_cfg, dict) else {}
                seconds = float(tcfg.get('seconds_right' if direcao == 'direita' else 'seconds_left', 1.2))
                speed_time = int(tcfg.get('speed', v_max))
                speed_time = max(v_min, min(v_max, speed_time))
                print(f"⏲️ Curva por tempo: {seconds:.2f}s @ {speed_time}")
                # Probe de direção por yaw
                ang0 = self.get_current_angle()
                if ang0 is not None:
                    self.mpu.enviar_comando(comando, {'velocidade': speed_time})
                    time.sleep(0.1)
                    self.parar()
                    ang1 = self.get_current_angle()
                    if ang1 is not None:
                        dyaw = self.calcular_diferenca_angular(ang0, ang1)
                        if (direcao == 'direita' and dyaw > 0) or (direcao == 'esquerda' and dyaw < 0):
                            comando = 'virar_esquerda' if comando == 'virar_direita' else 'virar_direita'
                            print("🔁 Auto-ajuste de direção (tempo/yaw): invertido")
                self.mpu.enviar_comando(comando, {'velocidade': speed_time})
                time.sleep(seconds)
                self.parar()
                time.sleep(pause_after)
                return True

            # Iniciar movimento contínuo de rotação (estratégia giroscópio)
            self.mpu.enviar_comando(comando, {'velocidade': max(v_min, min(v_max, int(v_max)))})

            # Aguardar alcance do ângulo de parada
            timeout = 25  # segundos máximo
            inicio = time.time()
            leituras_consecutivas_no_alvo = 0
            leituras_necessarias = 1
            leituras_consecutivas_falha = 0
            max_falhas_consecutivas = 15
            slowed_down = False
            last_valid_angle = None
            last_valid_time = None
            prev_diff = None
            micro_pulses = 0
            # Limites para filtrar leituras espúrias do yaw
            max_rate_allowed = float(turn_cfg.get('max_rate_deg_s', 180.0))
            max_jump_allowed = float(turn_cfg.get('max_jump_deg', 45.0))

            while time.time() - inicio < timeout:
                angulo_atual = self.get_current_angle()
                if angulo_atual is None:
                    leituras_consecutivas_falha += 1
                    print(f"  ⚠️ Falha ao obter ângulo ({leituras_consecutivas_falha}/{max_falhas_consecutivas})")
                    if leituras_consecutivas_falha >= max_falhas_consecutivas:
                        print("❌ Muitas falhas consecutivas, parando movimento")
                        break
                    continue
                else:
                    leituras_consecutivas_falha = 0

                # Calcular diferença angular até o ponto de parada
                diff = self.calcular_diferenca_angular(angulo_atual, angulo_parada)

                # Estimar taxa angular (graus/seg) com filtro anti-glitch
                now = time.time()
                if last_valid_angle is not None and last_valid_time is not None:
                    d_ang = self.calcular_diferenca_angular(last_valid_angle, angulo_atual)
                    dt = max(1e-3, now - last_valid_time)
                    est_rate = abs(d_ang / dt)
                    if dt < 0.2 and (est_rate > max_rate_allowed or abs(d_ang) > max_jump_allowed):
                        print(f"  ⚠️ Leitura yaw descartada (salto) d={d_ang:.1f}° em {dt*1000:.0f}ms (~{est_rate:.1f}°/s)")
                        time.sleep(0.02)
                        continue
                    rate = est_rate
                else:
                    rate = 0.0
                last_valid_angle, last_valid_time = angulo_atual, now

                print(f"Ângulo atual: {angulo_atual:.1f}°, Diferença para parada: {diff:.1f}°, Vel: ~{rate:.1f}°/s")

                # Progresso como deslocamento angular absoluto desde o início (0..180)
                prog = abs(self.calcular_diferenca_angular(angulo_inicial, angulo_atual))

                # Se cruzou o ponto de parada, frear imediatamente (evitar passar muito)
                sign_flipped = (prev_diff is not None) and ((prev_diff <= 0 and diff > 0) or (prev_diff >= 0 and diff < 0))
                elapsed = now - inicio
                near_win = float(turn_cfg.get('sign_flip_near_window_deg', 15.0))
                # Só dispara se estiver realmente perto do ponto antes de cruzar
                if (not simple_mode) and sign_flip_brake and sign_flipped and (elapsed > 0.4) and (abs(prev_diff) <= max(near_win, tol_stop * 3)):
                    print("🛑 Cruzou ponto de parada: freio imediato")
                    self.parar()
                    time.sleep(pause_after)
                    break

                prev_diff = diff

                # Segurança: se já girou muito além do previsto (> angulo_curva + 25°), interrompe
                if elapsed > 0.7 and rate > 5.0 and prog > (self.angulo_curva + 30):
                    print(f"⚠️ Progresso excessivo ({prog:.1f}° > {self.angulo_curva + 30}°), interrompendo para evitar loop")
                    self.parar()
                    time.sleep(pause_after)
                    break

                # Atualizar dinamicamente a compensação de inércia e ângulo de parada com base na taxa atual
                if dynamic_comp and rate > 1.0:
                    compensacao_ant = compensacao_inercia
                    compensacao_inercia = base_comp + k_rate * rate
                    angulo_parada = (angulo_alvo - (compensacao_inercia * sentido)) % 360
                    if abs(compensacao_inercia - compensacao_ant) >= 0.2:
                        print(f"⚙️ Reajuste comp_inercia: {compensacao_ant:.2f}° -> {compensacao_inercia:.2f}° | novo ponto de parada: {angulo_parada:.1f}°")

                # Verificar se chegou no ponto de parada antes de qualquer pulso creep
                if abs(diff) <= tol_stop:
                    leituras_consecutivas_no_alvo += 1
                    print(f"  ✅ Leitura {leituras_consecutivas_no_alvo}/{leituras_necessarias} no ponto de parada")
                    if leituras_consecutivas_no_alvo >= leituras_necessarias:
                        print("✅ Ponto de parada alcançado!")
                        break
                else:
                    leituras_consecutivas_no_alvo = 0

                # Controle de velocidade: modo simples ou detalhado
                if abs(diff) > tol_stop:
                    if simple_mode:
                        # Modo simples: rápido até sobrar slow_simple graus; na zona lenta, breve freio (se taxa alta) e pulsos curtos
                        if abs(diff) > slow_simple:
                            self.mpu.enviar_comando(comando, {'velocidade': v_max})
                        else:
                            rate_brk_th = float(turn_cfg.get('simple_rate_brake_thresh', 25.0))
                            if rate > rate_brk_th:
                                self.parar()
                                time.sleep(float(turn_cfg.get('simple_brake_pause_s', 0.09)))
                            pulse = float(turn_cfg.get('simple_pulse_s', 0.05))
                            pause = float(turn_cfg.get('simple_pause_s', 0.05))
                            self.mpu.enviar_comando(comando, {'velocidade': v_min})
                            time.sleep(pulse)
                            self.parar()
                            micro_pulses += 1
                            time.sleep(pause)
                            continue
                    else:
                        # Modo detalhado (original): proporcional + creep
                        if abs(diff) < th_slow:
                            # Creep mode: pulsos curtos quando muito próximo
                            creep_th = float(turn_cfg.get('creep_threshold_deg', 3.0))
                            if abs(diff) <= creep_th and getattr(self.mpu, 'serial_conn', None):
                                pulse = float(turn_cfg.get('creep_pulse_s', 0.06))
                                pause = float(turn_cfg.get('creep_pause_s', 0.05))
                                self.mpu.enviar_comando(comando, {'velocidade': v_min})
                                time.sleep(pulse)
                                self.parar()
                                micro_pulses += 1
                                time.sleep(pause)
                                # Recalcular imediatamente após o pulso
                                continue
                            else:
                                # Proporcional: mais perto => mais lento (limitado por v_min)
                                frac = max(0.0, min(1.0, abs(diff) / th_slow))
                                if slowdown_gamma != 1.0:
                                    frac = pow(frac, slowdown_gamma)
                                speed_target = int(v_min + k_speed * frac * (v_max - v_min))
                                self.mpu.enviar_comando(comando, {'velocidade': max(v_min, min(v_max, speed_target))})
                                slowed_down = True

                time.sleep(0.06)  # Amostrar mais rápido para reagir melhor

            # Parar movimento imediatamente
            self.parar()

            # Aguardar estabilização e obter ângulo final
            time.sleep(pause_after)  # tempo para estabilização
            angulo_final = self.get_current_angle()
            if angulo_final is not None:
                self.posicao_atual['angulo'] = angulo_final
                # Ajustar compensação de inércia baseada na taxa durante aproximação
                if slowed_down:
                    # já temos última 'rate'; use-a
                    compensacao_inercia = base_comp + k_rate * rate
                diff_final = self.calcular_diferenca_angular(angulo_final, angulo_alvo)
                print(f"Ângulo final: {angulo_final:.1f}°, Diferença do alvo: {diff_final:.1f}° (comp_inercia={compensacao_inercia:.2f}°; micro_pulses={micro_pulses})")

                # Micro ajuste, se ainda estiver fora da tolerância
                if abs(diff_final) > (tol_stop + 0.5) and getattr(self.mpu, 'serial_conn', None):
                    print("🪛 Microajuste de ângulo...")
                    cmd_micro = 'virar_direita' if diff_final > 0 else 'virar_esquerda'
                    # NOTA: invertido novamente devido à orientação do MPU
                    cmd_micro = 'virar_esquerda' if cmd_micro == 'virar_direita' else 'virar_direita'
                    self.mpu.enviar_comando(cmd_micro, {'velocidade': v_min})
                    time.sleep(0.08)
                    self.parar()
                    angulo_final2 = self.get_current_angle()
                    if angulo_final2 is not None:
                        self.posicao_atual['angulo'] = angulo_final2
                        diff_final2 = self.calcular_diferenca_angular(angulo_final2, angulo_alvo)
                        print(f"Ângulo pós-microajuste: {angulo_final2:.1f}°, Diferença: {diff_final2:.1f}°")

            return True

        except Exception as e:
            print(f"❌ Erro na curva de 90°: {e}")
            self.parar()
            return False

    def get_current_angle(self):
        """Obter o ângulo atual (yaw) do MPU6050 com retry"""
        for tentativa in range(3):
            status = self.mpu.obter_status_completo()
            if status and status.get('orientacao'):
                return status['orientacao']['yaw']
            print(f"  ⚠️ Tentativa {tentativa+1} falhou, tentando novamente...")
            time.sleep(0.05)  # Pequeno delay entre tentativas
        print("  ❌ Todas as tentativas falharam")
        return None

    def calcular_diferenca_angular(self, angulo_atual, angulo_alvo):
        """Calcular a menor diferença angular considerando wrap-around 0-360°"""
        diff = angulo_alvo - angulo_atual

        # Normalizar para -180 a +180
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        return diff

    def executar_rota_quadrada(self, lado_cm=100):
        """Executar rota quadrada (teste de navegação)"""
        try:
            print("🔲 EXECUTANDO ROTA QUADRADA")
            print("=" * 30)
            print(f"📏 Lado: {lado_cm}cm")

            rota = [
                ('frente', lado_cm),
                ('direita', 90),
                ('frente', lado_cm),
                ('direita', 90),
                ('frente', lado_cm),
                ('direita', 90),
                ('frente', lado_cm),
                ('direita', 90)
            ]

            for i, (tipo, valor) in enumerate(rota, 1):
                print(f"\n📍 Passo {i}/8: {tipo} {valor}")
                print(f"📍 Posição atual: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}, Ângulo={self.posicao_atual['angulo']:.1f}°")

                if tipo == 'frente':
                    if not self.mover_em_linha_reta(valor, 'frente'):
                        print("❌ Falha no movimento em linha reta")
                        return False
                elif tipo in ['direita', 'esquerda']:
                    if not self.virar_90_graus(tipo):
                        print("❌ Falha na curva")
                        return False

                time.sleep(1)  # Pausa entre movimentos

            print("✅ ROTA QUADRADA CONCLUÍDA!")
            print(f"Posição final: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}")
            return True
        except Exception as e:
            print(f"❌ Erro na rota quadrada: {e}")
            self.parar()
            return False

    def executar_rota_personalizada(self, comandos):
        """Executar rota personalizada"""
        print("🚀 EXECUTANDO ROTA PERSONALIZADA")
        print("=" * 35)

        for i, comando in enumerate(comandos, 1):
            print(f"\n📍 Comando {i}: {comando}")

            if comando['tipo'] == 'mover':
                if not self.mover_em_linha_reta(comando['distancia'], comando.get('direcao', 'frente')):
                    print("❌ Falha no movimento")
                    return False

            elif comando['tipo'] == 'virar':
                if not self.virar_90_graus(comando.get('direcao', 'direita')):
                    print("❌ Falha na curva")
                    return False

            time.sleep(1)

        print("✅ ROTA PERSONALIZADA CONCLUÍDA!")
        return True

    def mostrar_status(self):
        """Mostrar status atual"""
        status = self.mpu.obter_status_completo()

        print("\n📊 STATUS DO AGV")
        print("=" * 20)
        print(f"Posição: X={self.posicao_atual['x']:.1f}, Y={self.posicao_atual['y']:.1f}, Ângulo={self.posicao_atual['angulo']:.1f}°")
        print(f"🔋 Conectado: {'Sim' if status else 'Não'}")
        print(f"📏 Distância: {self.distancia_minima}cm (simulado)")

        if status and status['orientacao']:
            print(f"Yaw: {status['orientacao']['yaw']:.1f}°")
            print(f"Pitch: {status['orientacao']['pitch']:.1f}°")
            print(f"Roll: {status['orientacao']['roll']:.1f}°")
        print(f"🔄 Movimento: {'Sim' if status and status.get('movimento_detectado', False) else 'Não'}")

def main():
    """Função principal"""
    print("🎯 NAVEGAÇÃO BÁSICA AGV")
    print("=" * 25)

    # Configurações
    port = get_esp32_port()  # Porta do config.py

    # Criar navegação
    nav = BasicNavigation(esp32_port=port)

    # Inicializar
    if not nav.inicializar():
        return

    # Menu de opções
    while True:
        print("\n" + "="*40)
        print("🎮 MENU DE NAVEGAÇÃO")
        print("="*40)
        print("1. Teste em linha reta (50cm)")
        print("2. Teste de curva 90° (direita)")
        print("3. Teste de curva 90° (esquerda)")
        print("4. Executar rota quadrada")
        print("5. Mostrar status")
        print("6. Parar motores")
        print("0. Sair")
        print("="*40)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                nav.mover_em_linha_reta(50, 'frente')
            elif opcao == '2':
                nav.virar_90_graus('direita')
            elif opcao == '3':
                nav.virar_90_graus('esquerda')
            elif opcao == '4':
                nav.executar_rota_quadrada(50)
            elif opcao == '5':
                nav.mostrar_status()
            elif opcao == '6':
                nav.parar()
                print("🛑 Motores parados")
            elif opcao == '0':
                nav.parar()
                print("👋 Saindo...")
                break
            else:
                print("❌ Opção inválida")

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            nav.parar()
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            nav.parar()

if __name__ == "__main__":
    main()