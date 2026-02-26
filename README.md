# ✦ Braill'ie — Your Reading Assistant

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Pico-red)
![Language](https://img.shields.io/badge/language-Python%20%7C%20MicroPython-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

**A smart wearable glove that converts any PDF into real-time tactile braille.**  
*No special books. No braille printer. Just put on the glove and read.*

</div>

---

## 🧠 Problem Statement

Over **285 million people** worldwide are visually impaired, and among them, the deaf-blind community faces extreme barriers to accessing information. Braille texts are not mainstream — less than **1% of published books** exist in braille format.

**Braill'ie** solves this by turning *any digital text* into tactile braille feedback through a smart wearable glove — on any surface, on demand.

---

## 💡 What is Braill'ie?

Braill'ie is an **all-surface braille reading device** that:
- Reads any PDF file
- Tracks the glove's position on a page
- Sends the correct braille character to 6 finger actuators in real time
- Works on **any surface** — no special braille paper needed

---

## 🏗️ System Architecture

```
┌─────────────────┐        WebSocket         ┌──────────────────────┐
│   Braill'ie GUI │ ◄──────────────────────► │  Position Server     │
│  (Python/Tkinter)│                          │  (Python WebSocket)  │
└────────┬────────┘                          └──────────┬───────────┘
         │ Serial (USB)                                  │ I2C
         ▼                                              ▼
┌─────────────────┐                          ┌──────────────────────┐
│ Raspberry Pi    │                          │  MPU6050 + GY-271    │
│ Pico            │                          │  Sensor Fusion       │
└────────┬────────┘                          └──────────────────────┘
         │ GPIO
         ▼
┌─────────────────┐
│  6 Actuators    │
│  (Braille Dots) │
└─────────────────┘
```

---

## 🔧 Hardware Requirements

| Component | Purpose |
|-----------|---------|
| Raspberry Pi Pico | Main microcontroller |
| MPU6050 | Accelerometer + Gyroscope (position tracking) |
| GY-271 (QMC5883L) | Magnetometer/Compass (heading tracking) |
| 6x Voice Coil Actuators | Braille dot haptic feedback |
| Jumper Wires + Breadboard | Connections |
| Glove | Wearable base |

---

## 🔌 Wiring Diagram

### Sensors → Raspberry Pi Pico

| Sensor Pin | Pico Pin | Description |
|------------|----------|-------------|
| VCC (both sensors) | Pin 36 (3.3V) | Power |
| GND (both sensors) | Pin 38 (GND) | Ground |
| SDA (both sensors) | GP4 — Pin 6 | I2C Data |
| SCL (both sensors) | GP5 — Pin 7 | I2C Clock |

> Both MPU6050 and GY-271 share the same I2C bus.  
> MPU6050 address: `0x68` | GY-271 address: `0x0D`

---

## 💻 Software Requirements

### On your Laptop
```bash
pip install pyserial PyMuPDF websockets
```

### On Raspberry Pi Pico
- MicroPython firmware installed
- No extra libraries needed

---

## 🚀 How to Run

### Step 1 — Flash Pico
Upload `sensor_fusion.py` to your Raspberry Pi Pico using Thonny IDE.

### Step 2 — Start Position Server
```bash
python position_server.py
```
You should see:
```
Braill'ie Position Server
WebSocket running on ws://localhost:8765
Waiting for GUI to connect...
```

### Step 3 — Launch GUI
Open a second terminal:
```bash
python braillie_gui.py
```

### Step 4 — Use the App
1. **Welcome Screen** → Click Get Started
2. **Calibrate** → Place glove at top-left corner of page → Click Calibrate
3. **Open PDF** → Browse and load any PDF file
4. **Reading** → Glove position controls which character is sent to actuators

---

## 📁 Project Structure

```
braillie-reader/
│
├── braillie_gui.py          # Main GUI application (Python/Tkinter)
├── position_server.py       # WebSocket position server
│
├── pico/
│   ├── sensor_fusion.py     # MPU6050 + GY-271 complementary filter
│   ├── mpu6050_test.py      # MPU6050 standalone test
│   ├── gy271_test.py        # GY-271 standalone test
│   └── i2c_scanner.py       # I2C device scanner
│
└── README.md
```

---

## 🔬 Sensor Fusion

Braill'ie uses a **Complementary Filter** to combine data from both sensors:

```
MPU6050  →  Pitch & Roll angles  (accelerometer + gyroscope)
GY-271   →  Heading / Direction  (magnetometer)
              ↓
    Complementary Filter (α = 0.95)
              ↓
    Stable, repeatable position index
```

This ensures that returning to the same physical position always produces the same position index — essential for accurate braille character selection.

---

## 🌍 SDG Alignment

| SDG | Goal | How Braill'ie Helps |
|-----|------|-------------------|
| SDG 4 | Quality Education | Access to any text for visually impaired |
| SDG 10 | Reduced Inequalities | Closes disability access gap |
| SDG 3 | Good Health & Wellbeing | Independence for deaf-blind individuals |

---

## 🏆 Key Innovations

- **Any-surface reading** — works on any page, table, or surface
- **Software-defined braille** — no embossed braille needed
- **Position-aware** — glove location determines character, not just sequential playback
- **Dual-sensor fusion** — eliminates drift and noise for repeatable positioning
- **Real-time WebSocket architecture** — low latency, scalable

---

## 👥 Team

**Team Quantum**  
Hackathon Project — 2026
    SRIVAN REDDY
    HARITEIJ GHANTOJI
    SANCHITA.N
    DEVI KRISHNA MANOJ

---

## 📄 License

MIT License — feel free to build on this!
