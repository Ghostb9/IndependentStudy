# 🎛️ Servo Control Panel

A Tkinter-based GUI for controlling two servos via a PCA9685 PWM driver on Raspberry Pi. Includes manual control and a playable Rock Paper Scissors game where the servos physically act out the CPU's move.

---

## Features

- **Servo 1 & 2 tabs** — slider + trigger/reset buttons for each channel
- **Rock Paper Scissors** — play against the CPU; servos fire based on the CPU's hand:
  - 🪨 Rock → both servos fire
  - 📄 Paper → no servos fire
  - ✂️ Scissors → servo 1 fires
- **Demo mode** — runs without hardware, prints moves to console for testing

---

## Hardware

| Component | Detail |
|-----------|--------|
| Board | Raspberry Pi (any model with I2C) |
| Driver | PCA9685 16-channel PWM |
| Servos | Connected to channels 0 and 1 |
| Pulse range | 400 µs – 2600 µs |
| Actuation range | 270° |

Servos start at **270°** and move to **0°** when triggered.

---

## Installation

```bash
pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
python3 servo_gui.py
```

> Tkinter is included with most Raspberry Pi OS Python installs. If missing: `sudo apt install python3-tk`

---

## Usage

1. Run the script — three tabs appear
2. **Tab 1 / Tab 2** — drag the slider or hit Trigger/Reset for each servo
3. **Tab 3** — pick Rock, Paper, or Scissors and hit **SHOOT!**
