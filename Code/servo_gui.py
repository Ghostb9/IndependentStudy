##Independent Study



##imports

import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time



##Hardware setup
try:
    import board, busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo as adafruit_servo

    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50

    SERVO_KWARGS = dict(actuation_range=270, min_pulse=400, max_pulse=2600)
    servo1 = adafruit_servo.Servo(pca.channels[0], **SERVO_KWARGS)
    servo2 = adafruit_servo.Servo(pca.channels[1], **SERVO_KWARGS)
    HARDWARE = True
except Exception as e:
    print(f"[WARNING] Hardware not found — running in demo mode: {e}")
    HARDWARE = False

    class FakeServo:
        def __init__(self, label):
            self.label = label
            self.angle = 270
        def set_angle(self, a):
            self.angle = a
            print(f"[DEMO] {self.label} → {a}°")

    servo1 = FakeServo("Servo 1")
    servo2 = FakeServo("Servo 2")

START_ANGLE   = 270
TRIGGER_ANGLE = 0

def move_servo(s, angle):
    if HARDWARE:
        s.angle = angle
    else:
        s.set_angle(angle)

def reset_servos():
    move_servo(servo1, START_ANGLE)
    move_servo(servo2, START_ANGLE)


## stuff for gui
BG       = "#0d0d0f"
PANEL    = "#16161a"
ACCENT1  = "#e8ff47"   
ACCENT2  = "#47c5ff"   
ACCENT3  = "#ff6b6b"   
FG       = "#f0f0f0"
SUBTLE   = "#555566"
FONT_H   = ("Courier New", 13, "bold")
FONT_B   = ("Courier New", 11)
FONT_SM  = ("Courier New", 9)

RPS_EMOJIS  = {"ROCK": "🪨", "PAPER": "📄", "SCISSORS": "✂️"}
RPS_CHOICES = list(RPS_EMOJIS)
RPS_OUTCOMES = {
    ("ROCK",    "ROCK"):    "draw",
    ("ROCK",    "PAPER"):   "lose",
    ("ROCK",    "SCISSORS"):"win",
    ("PAPER",   "ROCK"):    "win",
    ("PAPER",   "PAPER"):   "draw",
    ("PAPER",   "SCISSORS"):"lose",
    ("SCISSORS","ROCK"):    "lose",
    ("SCISSORS","PAPER"):   "win",
    ("SCISSORS","SCISSORS"):"draw",
}


##main class
class ServoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SERVO CONTROL PANEL")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    ##gui layout
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=16)
        hdr.pack(fill="x", padx=24)
        tk.Label(hdr, text="◈  SERVO CONTROL", font=("Courier New", 17, "bold"),
                 bg=BG, fg=ACCENT1).pack(side="left")
        self._hw_dot = tk.Label(hdr, text="● LIVE" if HARDWARE else "● DEMO",
                                font=FONT_SM, bg=BG,
                                fg=ACCENT1 if HARDWARE else SUBTLE)
        self._hw_dot.pack(side="right", padx=4)

        # Separator
        tk.Frame(self, bg=ACCENT1, height=1).pack(fill="x", padx=24)

        # Three tabs
        nb_frame = tk.Frame(self, bg=BG)
        nb_frame.pack(fill="both", expand=True, padx=24, pady=18)

        self._tabs = {}
        self._tab_btns = {}
        tab_bar = tk.Frame(nb_frame, bg=BG)
        tab_bar.pack(fill="x")

        self._content = tk.Frame(nb_frame, bg=PANEL, bd=0, relief="flat")
        self._content.pack(fill="both", expand=True, pady=(0, 4))

        tabs_info = [
            ("1  SERVO 1",   ACCENT1, self._build_servo1_tab),
            ("2  SERVO 2",   ACCENT2, self._build_servo2_tab),
            ("3  ROCK PAPER SCISSORS", ACCENT3, self._build_rps_tab),
        ]
        for key, color, builder in tabs_info:
            btn = tk.Button(
                tab_bar, text=key, font=FONT_H,
                bg=BG, fg=SUBTLE, relief="flat", bd=0,
                padx=14, pady=8, cursor="hand2",
                activebackground=BG, activeforeground=color,
                command=lambda k=key, c=color, b=builder: self._switch_tab(k, c, b)
            )
            btn.pack(side="left")
            self._tab_btns[key] = (btn, color)

        # Build all tab frames 
        self._frames = {}
        for key, color, builder in tabs_info:
            frame = tk.Frame(self._content, bg=PANEL)
            builder(frame, color)
            self._frames[key] = frame

        # Activate first tab
        self._active_tab = None
        self._switch_tab("1  SERVO 1", ACCENT1, self._build_servo1_tab)

        # Footer
        tk.Frame(self, bg=SUBTLE, height=1).pack(fill="x", padx=24)
        tk.Label(self, text="servos start at 270°  ·  activated → 0°",
                 font=FONT_SM, bg=BG, fg=SUBTLE).pack(pady=6)

    def _switch_tab(self, key, color, builder):
        if self._active_tab == key:
            return
        self._active_tab = key
        for k, (btn, c) in self._tab_btns.items():
            if k == key:
                btn.config(fg=c, bg=PANEL)
            else:
                btn.config(fg=SUBTLE, bg=BG)
        for k, frame in self._frames.items():
            if k == key:
                frame.pack(fill="both", expand=True, padx=20, pady=20)
            else:
                frame.pack_forget()

    ## first servo
    def _build_servo1_tab(self, f, color):
        self._s1_angle = tk.DoubleVar(value=START_ANGLE)
        self._s1_status = tk.StringVar(value="IDLE  —  270°")

        tk.Label(f, text="CHANNEL 0  /  SERVO 1", font=FONT_H,
                 bg=PANEL, fg=color).pack(pady=(0, 12))

        self._s1_display = tk.Label(f, text="270°",
                                    font=("Courier New", 42, "bold"),
                                    bg=PANEL, fg=color)
        self._s1_display.pack()

        bar = tk.Scale(f, from_=0, to=270, orient="horizontal",
                       variable=self._s1_angle,
                       command=self._on_s1_slide,
                       bg=PANEL, fg=FG, troughcolor=BG,
                       activebackground=color, highlightthickness=0,
                       sliderrelief="flat", sliderlength=20, length=340,
                       tickinterval=90, font=FONT_SM)
        bar.pack(pady=12)

        btn_row = tk.Frame(f, bg=PANEL)
        btn_row.pack(pady=6)
        self._make_btn(btn_row, "▶  TRIGGER (→ 0°)", color,
                       lambda: self._servo_action(servo1, TRIGGER_ANGLE, self._s1_angle,
                                                   self._s1_display, self._s1_status)
                       ).pack(side="left", padx=6)
        self._make_btn(btn_row, "↺  RESET (→ 270°)", SUBTLE,
                       lambda: self._servo_action(servo1, START_ANGLE, self._s1_angle,
                                                   self._s1_display, self._s1_status)
                       ).pack(side="left", padx=6)

        tk.Label(f, textvariable=self._s1_status, font=FONT_SM,
                 bg=PANEL, fg=SUBTLE).pack(pady=4)

    def _on_s1_slide(self, val):
        angle = int(float(val))
        self._s1_display.config(text=f"{angle}°")
        move_servo(servo1, angle)
        self._s1_status.set(f"MANUAL  —  {angle}°")

   ##second servo
    def _build_servo2_tab(self, f, color):
        self._s2_angle = tk.DoubleVar(value=START_ANGLE)
        self._s2_status = tk.StringVar(value="IDLE  —  270°")

        tk.Label(f, text="CHANNEL 1  /  SERVO 2", font=FONT_H,
                 bg=PANEL, fg=color).pack(pady=(0, 12))

        self._s2_display = tk.Label(f, text="270°",
                                    font=("Courier New", 42, "bold"),
                                    bg=PANEL, fg=color)
        self._s2_display.pack()

        bar = tk.Scale(f, from_=0, to=270, orient="horizontal",
                       variable=self._s2_angle,
                       command=self._on_s2_slide,
                       bg=PANEL, fg=FG, troughcolor=BG,
                       activebackground=color, highlightthickness=0,
                       sliderrelief="flat", sliderlength=20, length=340,
                       tickinterval=90, font=FONT_SM)
        bar.pack(pady=12)

        btn_row = tk.Frame(f, bg=PANEL)
        btn_row.pack(pady=6)
        self._make_btn(btn_row, "▶  TRIGGER (→ 0°)", color,
                       lambda: self._servo_action(servo2, TRIGGER_ANGLE, self._s2_angle,
                                                   self._s2_display, self._s2_status)
                       ).pack(side="left", padx=6)
        self._make_btn(btn_row, "↺  RESET (→ 270°)", SUBTLE,
                       lambda: self._servo_action(servo2, START_ANGLE, self._s2_angle,
                                                   self._s2_display, self._s2_status)
                       ).pack(side="left", padx=6)

        tk.Label(f, textvariable=self._s2_status, font=FONT_SM,
                 bg=PANEL, fg=SUBTLE).pack(pady=4)

    def _on_s2_slide(self, val):
        angle = int(float(val))
        self._s2_display.config(text=f"{angle}°")
        move_servo(servo2, angle)
        self._s2_status.set(f"MANUAL  —  {angle}°")

    ##action for servo
    def _servo_action(self, servo, angle, var, display_lbl, status_var):
        move_servo(servo, angle)
        var.set(angle)
        display_lbl.config(text=f"{angle}°")
        status_var.set(f"{'TRIGGERED' if angle == TRIGGER_ANGLE else 'RESET'}  —  {angle}°")

    ## rock, paper, scissors gui
    def _build_rps_tab(self, f, color):
        self._rps_playing = False

        tk.Label(f, text="ROCK  ·  PAPER  ·  SCISSORS", font=FONT_H,
                 bg=PANEL, fg=color).pack(pady=(0, 4))
        tk.Label(f,
                 text="🪨 ROCK = both servos fire  |  📄 PAPER = none  |  ✂️ SCISSORS = servo 1",
                 font=FONT_SM, bg=PANEL, fg=SUBTLE).pack(pady=(0, 12))

        # Player pick
        pick_row = tk.Frame(f, bg=PANEL)
        pick_row.pack()
        tk.Label(pick_row, text="YOUR PICK:", font=FONT_B,
                 bg=PANEL, fg=FG).pack(side="left", padx=(0, 10))
        self._rps_choice = tk.StringVar(value="ROCK")
        for move in RPS_CHOICES:
            rb = tk.Radiobutton(pick_row, text=f"{RPS_EMOJIS[move]} {move}",
                                variable=self._rps_choice, value=move,
                                font=FONT_B, bg=PANEL, fg=FG,
                                selectcolor=BG, activebackground=PANEL,
                                activeforeground=color, cursor="hand2")
            rb.pack(side="left", padx=8)

        # Shoot button
        self._rps_btn = self._make_btn(f, "🎲  SHOOT!", color, self._rps_shoot)
        self._rps_btn.pack(pady=14)

        # Result area
        res_frame = tk.Frame(f, bg=BG, padx=16, pady=12)
        res_frame.pack(fill="x", pady=(0, 4))

        self._rps_you   = tk.Label(res_frame, text="YOU\n—", font=("Courier New", 22, "bold"),
                                   bg=BG, fg=FG, width=10)
        self._rps_you.pack(side="left", expand=True)

        self._rps_vs    = tk.Label(res_frame, text="VS", font=("Courier New", 14, "bold"),
                                   bg=BG, fg=SUBTLE)
        self._rps_vs.pack(side="left")

        self._rps_cpu   = tk.Label(res_frame, text="CPU\n—", font=("Courier New", 22, "bold"),
                                   bg=BG, fg=FG, width=10)
        self._rps_cpu.pack(side="left", expand=True)

        self._rps_result = tk.Label(f, text="", font=("Courier New", 16, "bold"),
                                    bg=PANEL, fg=color)
        self._rps_result.pack(pady=4)

        self._rps_servo_lbl = tk.Label(f, text="", font=FONT_SM,
                                       bg=PANEL, fg=SUBTLE)
        self._rps_servo_lbl.pack()

    def _rps_shoot(self):
        if self._rps_playing:
            return
        self._rps_playing = True
        self._rps_btn.config(state="disabled")
        player = self._rps_choice.get()
        threading.Thread(target=self._rps_animate, args=(player,), daemon=True).start()

    def _rps_animate(self, player):
        # Countdown flash
        for countdown in ["3…", "2…", "1…", "SHOOT!"]:
            self.after(0, lambda t=countdown: self._rps_result.config(text=t, fg=ACCENT3))
            time.sleep(0.5)

        cpu = random.choice(RPS_CHOICES)
        outcome = RPS_OUTCOMES[(player, cpu)]

        # Update UI
        p_txt = f"YOU\n{RPS_EMOJIS[player]}\n{player}"
        c_txt = f"CPU\n{RPS_EMOJIS[cpu]}\n{cpu}"
        result_map = {
            "win":  ("YOU WIN! 🎉", ACCENT1),
            "lose": ("CPU WINS! 💀", ACCENT3),
            "draw": ("DRAW!  🤝",   ACCENT2),
        }
        rtxt, rclr = result_map[outcome]

        self.after(0, lambda: self._rps_you.config(text=p_txt))
        self.after(0, lambda: self._rps_cpu.config(text=c_txt))
        self.after(0, lambda: self._rps_result.config(text=rtxt, fg=rclr))

        # Fire servos based on CPU move
        servo_msg = self._fire_rps_servos(cpu)
        self.after(0, lambda: self._rps_servo_lbl.config(text=servo_msg))

        # Reset servos after 1.5 s
        time.sleep(1.5)
        reset_servos()
        self.after(0, lambda: self._rps_servo_lbl.config(
            text=servo_msg + "  ↺ servos reset"))

        self.after(0, lambda: self._rps_btn.config(state="normal"))
        self._rps_playing = False

    def _fire_rps_servos(self, cpu_move):
        """Activate servos according to the CPU's move (what the hand robot shows)."""
        if cpu_move == "ROCK":          # both fire
            move_servo(servo1, TRIGGER_ANGLE)
            move_servo(servo2, TRIGGER_ANGLE)
            return "⚙️  servo 1 + servo 2 fired  (ROCK)"
        elif cpu_move == "PAPER":       # none fire
            move_servo(servo1, START_ANGLE)
            move_servo(servo2, START_ANGLE)
            return "⚙️  no servos fired  (PAPER)"
        else:                            # SCISSORS – servo 1 only
            move_servo(servo1, TRIGGER_ANGLE)
            move_servo(servo2, START_ANGLE)
            return "⚙️  servo 1 fired  (SCISSORS)"

    ##gui utlity
    @staticmethod
    def _make_btn(parent, text, color, command):
        return tk.Button(
            parent, text=text, command=command,
            font=FONT_H, bg=BG, fg=color,
            activebackground=color, activeforeground=BG,
            relief="flat", bd=0, padx=16, pady=8,
            cursor="hand2"
        )

    def _on_close(self):
        reset_servos()
        if HARDWARE:
            pca.deinit()
        self.destroy()


## run app
if __name__ == "__main__":
    app = ServoApp()
    app.mainloop()
