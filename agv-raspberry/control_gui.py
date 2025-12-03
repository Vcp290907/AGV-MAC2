"""
GUI de controle para ESP32 Garra usando esp32_control.py
Permite controlar os 5 servos e criar/executar sequências
"""

import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging

# Importar controlador ESP32
try:
    from esp32_control import get_esp32_garra_controller
except ImportError as e:
    print(f"Erro ao importar esp32_control: {e}")
    print("Certifique-se de que esp32_control.py está no mesmo diretório")
    raise

logging.basicConfig(level=logging.INFO)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 Garra Controller")
        self.geometry("780x460")
        
        # Usar esp32_control ao invés de conexão serial direta
        self.esp32 = None
        self.connected = False
        
        # sequence state
        self.sequence = []  # list of {angles:{name:int}, pause_ms:int}
        self.seq_running = False
        self._runner_thread = None
        self._stop_event = threading.Event()
        
        # fixed servo order for move commands and UI
        self.servo_order = ["giro", "um", "dois", "garra", "servo3"]
        
        self._build_ui()
        # Tentar conectar automaticamente
        self.after(500, self._auto_connect)

    def _build_ui(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Top: connection status and controls
        top = ttk.Frame(frm)
        top.pack(fill=tk.X)

        self.status_label = ttk.Label(top, text="⚪ Desconectado", font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(top, text="Conectar", command=self._connect_toggle)
        self.connect_btn.pack(side=tk.LEFT, padx=6)

        ttk.Button(top, text="Status", command=self._request_status).pack(side=tk.RIGHT, padx=(0,6))

        # Middle: sliders
        mid = ttk.Frame(frm)
        mid.pack(fill=tk.X, pady=(10,8))

        self.scales = {}
        labels = [("giro", 30), ("um", 90), ("dois", 160), ("garra", 70), ("servo3", 90)]
        for name, default in labels:
            f = ttk.Frame(mid)
            f.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=6)
            ttk.Label(f, text=name).pack()
            var = tk.IntVar(value=default)
            s = tk.Scale(f, from_=0, to=180, orient=tk.VERTICAL, variable=var, length=200)
            s.pack()
            # call when slider moves to potentially trigger live update (debounced)
            s.config(command=lambda val, name=name: self._on_scale_change(name, val))
            val_lbl = ttk.Label(f, textvariable=var)
            val_lbl.pack()
            self.scales[name] = var

        # Send MOVE button and Live update toggle
        send_frame = ttk.Frame(frm)
        send_frame.pack(fill=tk.X)
        ttk.Button(send_frame, text="Send MOVE", command=self._send_move).pack(side=tk.LEFT)
        ttk.Button(send_frame, text="Home (Init)", command=self._home).pack(side=tk.LEFT, padx=6)
        # Live update checkbox: when enabled, changing sliders will auto-send MOVE (debounced)
        self.live_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(send_frame, text="Live update", variable=self.live_var).pack(side=tk.LEFT, padx=8)
        # placeholder for scheduled job id
        self._auto_send_job = None

        # Sequence builder / runner
        seq_frame = ttk.LabelFrame(frm, text="Sequence")
        seq_frame.pack(fill=tk.BOTH, expand=False, pady=(8, 8))

        # Controls row: pause and repeats
        controls_row = ttk.Frame(seq_frame)
        controls_row.pack(fill=tk.X, padx=6, pady=(6, 2))

        ttk.Label(controls_row, text="Pause (ms):").pack(side=tk.LEFT)
        self.pause_var = tk.IntVar(value=1000)
        ttk.Entry(controls_row, textvariable=self.pause_var, width=8).pack(side=tk.LEFT, padx=(4, 10))

        ttk.Label(controls_row, text="Repeats:").pack(side=tk.LEFT)
        self.repeat_var = tk.IntVar(value=1)
        ttk.Entry(controls_row, textvariable=self.repeat_var, width=6).pack(side=tk.LEFT, padx=(4, 10))

        ttk.Button(controls_row, text="Add step (current)", command=self._add_step_current).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(controls_row, text="Remove", command=self._remove_step).pack(side=tk.LEFT)
        ttk.Button(controls_row, text="Up", command=self._move_step_up).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(controls_row, text="Down", command=self._move_step_down).pack(side=tk.LEFT, padx=(6, 10))
        ttk.Button(controls_row, text="Clear", command=self._clear_sequence).pack(side=tk.LEFT)

        ttk.Button(controls_row, text="Save...", command=self._save_sequence).pack(side=tk.RIGHT)
        ttk.Button(controls_row, text="Load...", command=self._load_sequence).pack(side=tk.RIGHT, padx=(0, 6))

        # Treeview for steps
        tree_row = ttk.Frame(seq_frame)
        tree_row.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 6))

        columns = self.servo_order + ["pause_ms"]
        self.seq_tree = ttk.Treeview(tree_row, columns=columns, show="headings", height=6)
        for col in columns:
            self.seq_tree.heading(col, text=col)
            self.seq_tree.column(col, width=80, anchor=tk.CENTER)
        self.seq_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_row, orient=tk.VERTICAL, command=self.seq_tree.yview)
        self.seq_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Run/Stop buttons
        run_row = ttk.Frame(seq_frame)
        run_row.pack(fill=tk.X, padx=6, pady=(0, 6))
        self.run_btn = ttk.Button(run_row, text="Run sequence", command=self._run_sequence)
        self.stop_btn = ttk.Button(run_row, text="Stop", command=self._stop_sequence, state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT)
        self.stop_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Log area
        log_frame = ttk.Frame(frm)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10,0))
        self.log = tk.Text(log_frame, height=8)
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.configure(state=tk.DISABLED)

    def _auto_connect(self):
        """Tenta conectar automaticamente ao ESP32 Garra"""
        try:
            self.esp32 = get_esp32_garra_controller()
            if self.esp32.connect():
                self.connected = True
                self.status_label.config(text="🟢 Conectado", foreground="green")
                self.connect_btn.config(text="Desconectar")
                self._log(f"✅ Conectado ao ESP32 Garra em {self.esp32.port}")
            else:
                self.status_label.config(text="🔴 Erro de conexão", foreground="red")
                self._log("❌ Falha ao conectar")
        except Exception as e:
            self.status_label.config(text="🔴 Erro", foreground="red")
            self._log(f"❌ Erro: {e}")

    def _connect_toggle(self):
        """Conecta ou desconecta do ESP32"""
        if self.connected:
            if self.esp32:
                self.esp32.disconnect()
            self.connected = False
            self.status_label.config(text="⚪ Desconectado", foreground="black")
            self.connect_btn.config(text="Conectar")
            self._log("Desconectado")
        else:
            self._auto_connect()

    def _send_move(self):
        """Envia comando move_servos usando o formato JSON"""
        if not self.connected or not self.esp32:
            messagebox.showerror("Erro", "ESP32 não conectado")
            return
        try:
            command = {
                "comando": "move_servos",
                "a": int(self.scales['giro'].get()),
                "b": int(self.scales['um'].get()),
                "c": int(self.scales['dois'].get()),
                "d": int(self.scales['garra'].get()),
                "e": int(self.scales['servo3'].get())
            }
            response = self.esp32._send_command(command)
            if response and response.get("status") == "success":
                self._log(f"✅ Servos movidos: a={command['a']}, b={command['b']}, c={command['c']}, d={command['d']}, e={command['e']}")
            else:
                self._log(f"❌ Falha ao mover servos: {response}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self._log(f"❌ Erro: {e}")

    def _on_scale_change(self, name, val):
        # Update IntVar to keep label in sync (Scale already does this) but ensure int
        try:
            self.scales[name].set(int(float(val)))
        except Exception:
            pass
        # If live update is enabled and connected, debounce a send
        if self.live_var.get() and self.connected:
            self._schedule_auto_send()

    def _schedule_auto_send(self, delay_ms=200):
        # Debounce using Tk's after: cancel previous scheduled send and schedule a new one
        if hasattr(self, '_auto_send_job') and self._auto_send_job is not None:
            try:
                self.after_cancel(self._auto_send_job)
            except Exception:
                pass
        self._auto_send_job = self.after(delay_ms, self._auto_send_move)

    def _auto_send_move(self):
        # Called by after() when debounce period passed
        try:
            self._send_move()
        finally:
            self._auto_send_job = None

    # -------- Sequence helpers --------
    def _current_angles(self):
        # Build dict of current slider values in fixed order
        angles = {}
        for name in self.servo_order:
            if name in self.scales:
                angles[name] = int(self.scales[name].get())
        return angles

    def _add_step_current(self):
        try:
            pause_ms = int(self.pause_var.get())
        except Exception:
            pause_ms = 1000
            self.pause_var.set(pause_ms)
        step = {"angles": self._current_angles(), "pause_ms": pause_ms}
        self.sequence.append(step)
        self._refresh_seq_view()

    def _remove_step(self):
        sel = list(self.seq_tree.selection())
        if not sel:
            return
        # remove from end to start to keep indices valid
        indices = sorted([self.seq_tree.index(i) for i in sel], reverse=True)
        for idx in indices:
            if 0 <= idx < len(self.sequence):
                self.sequence.pop(idx)
        self._refresh_seq_view()

    def _move_step_up(self):
        sel = self.seq_tree.selection()
        if not sel:
            return
        idx = self.seq_tree.index(sel[0])
        if idx > 0:
            self.sequence[idx-1], self.sequence[idx] = self.sequence[idx], self.sequence[idx-1]
            self._refresh_seq_view(select_index=idx-1)

    def _move_step_down(self):
        sel = self.seq_tree.selection()
        if not sel:
            return
        idx = self.seq_tree.index(sel[0])
        if idx < len(self.sequence)-1:
            self.sequence[idx+1], self.sequence[idx] = self.sequence[idx], self.sequence[idx+1]
            self._refresh_seq_view(select_index=idx+1)

    def _clear_sequence(self):
        self.sequence.clear()
        self._refresh_seq_view()

    def _refresh_seq_view(self, select_index: int | None = None):
        # clear tree
        for item in self.seq_tree.get_children():
            self.seq_tree.delete(item)
        # repopulate
        for step in self.sequence:
            values = [step["angles"].get(name, 0) for name in self.servo_order]
            values.append(step.get("pause_ms", 0))
            self.seq_tree.insert("", tk.END, values=values)
        # restore selection
        if select_index is not None and 0 <= select_index < len(self.sequence):
            iid = self.seq_tree.get_children()[select_index]
            self.seq_tree.selection_set(iid)
            self.seq_tree.see(iid)

    def _save_sequence(self):
        if not self.sequence:
            messagebox.showinfo("Save sequence", "No steps to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.sequence, f, indent=2)
            self._log(f"Saved sequence to {path}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def _load_sequence(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json"), ("All files","*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # basic validation
            seq = []
            for item in data:
                angles = item.get("angles", {})
                pause_ms = int(item.get("pause_ms", 1000))
                # keep only known keys
                clean = {name: int(angles.get(name, 0)) for name in self.servo_order if name in angles}
                seq.append({"angles": clean, "pause_ms": pause_ms})
            self.sequence = seq
            self._refresh_seq_view()
            self._log(f"Loaded sequence from {path}")
        except Exception as e:
            messagebox.showerror("Load error", str(e))

    def _build_move_cmd(self, angles: dict[str, int]) -> dict:
        """Constrói comando JSON para move_servos"""
        # Mapear nomes para a, b, c, d, e
        return {
            "comando": "move_servos",
            "a": int(angles.get('giro', 0)),
            "b": int(angles.get('um', 0)),
            "c": int(angles.get('dois', 0)),
            "d": int(angles.get('garra', 0)),
            "e": int(angles.get('servo3', 0))
        }

    def _run_sequence(self):
        if self.seq_running:
            return
        if not self.sequence:
            messagebox.showinfo("Executar sequência", "Nenhuma etapa para executar.")
            return
        if not self.connected or not self.esp32:
            messagebox.showerror("Erro", "ESP32 não conectado")
            return
        try:
            repeats = max(1, int(self.repeat_var.get()))
        except Exception:
            repeats = 1
            self.repeat_var.set(repeats)
        self.seq_running = True
        self._stop_event.clear()
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        # start thread
        self._runner_thread = threading.Thread(target=self._runner, args=(repeats,), daemon=True)
        self._runner_thread.start()

    def _stop_sequence(self):
        if not self.seq_running:
            return
        self._stop_event.set()
        self._log("Stopping sequence...")

    def _runner(self, repeats: int):
        """Executa sequência em thread separada"""
        try:
            for r in range(repeats):
                if self._stop_event.is_set():
                    break
                self._log(f"Sequência execução {r+1}/{repeats}")
                for idx, step in enumerate(self.sequence):
                    if self._stop_event.is_set():
                        break
                    angles = step["angles"]
                    command = self._build_move_cmd(angles)
                    try:
                        response = self.esp32._send_command(command)
                        if response and response.get("status") == "success":
                            self._log(f"✅ Passo {idx+1}: a={command['a']}, b={command['b']}, c={command['c']}, d={command['d']}, e={command['e']}")
                        else:
                            self._log(f"❌ Falha no passo {idx+1}: {response}")
                            self._stop_event.set()
                            break
                    except Exception as e:
                        self._log(f"❌ Erro no envio: {e}")
                        self._stop_event.set()
                        break
                    # wait for pause
                    pause_ms = int(step.get("pause_ms", 0))
                    # sleep in small chunks to allow responsive stop
                    waited = 0
                    chunk = 50
                    while waited < pause_ms and not self._stop_event.is_set():
                        time.sleep(min(chunk, max(0, pause_ms - waited)) / 1000.0)
                        waited += chunk
                if self._stop_event.is_set():
                    break
        finally:
            self.seq_running = False
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self._log("Sequência finalizada.")

    def _stop_sequence(self):
        if not self.seq_running:
            return
        self._stop_event.set()
        self._log("Parando sequência...")

    def _request_status(self):
        """Solicita status do ESP32"""
        if not self.connected or not self.esp32:
            messagebox.showerror("Erro", "ESP32 não conectado")
            return
        try:
            response = self.esp32._send_command({"comando": "status"})
            if response:
                self._log(f"📥 Status: {response}")
                # Tentar atualizar sliders se houver informações de ângulos
                if "angles" in response:
                    for name, val in response["angles"].items():
                        if name in self.scales:
                            self.scales[name].set(int(val))
            else:
                self._log("❌ Sem resposta de status")
        except Exception as e:
            self._log(f"❌ Erro ao solicitar status: {e}")

    def _home(self):
        # set sliders to defaults matching sketch startup
        defaults = {"giro":30, "um":165, "dois":165, "garra":73, "servo3":90}
        for k, v in defaults.items():
            self.scales[k].set(v)
        self._log("Sliders ajustados para posições padrão/home")

    def _log(self, text):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)


if __name__ == '__main__':
    app = App()
    app.mainloop()
