# Braill'ie — Sensor Fusion
# MPU6050 (Accel + Gyro) + GY-271 (Magnetometer)
# Complementary Filter → gives stable, repeatable position
#
# When you move to a position → get a consistent value
# When you return to same position → get same value again
#
# Run this on Raspberry Pi Pico via Thonny

from machine import I2C, Pin
import time
import math

# ─────────────────────────────────────────
# I2C SETUP
# ─────────────────────────────────────────
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

MPU = 0x68   # MPU6050 address
QMC = 0x0D   # GY-271 address

# ─────────────────────────────────────────
# INITIALIZE SENSORS
# ─────────────────────────────────────────
def init_sensors():
    # Wake up MPU6050
    i2c.writeto_mem(MPU, 0x6B, b'\x00')
    # Set accelerometer range to ±2g
    i2c.writeto_mem(MPU, 0x1C, b'\x00')
    # Set gyroscope range to ±250°/s
    i2c.writeto_mem(MPU, 0x1B, b'\x00')

    # Initialize QMC5883L
    i2c.writeto_mem(QMC, 0x0B, b'\x01')  # reset period
    i2c.writeto_mem(QMC, 0x09, b'\x1D')  # continuous, 200Hz, 8G, 512 OSR
    print("✔ Both sensors initialized!")

# ─────────────────────────────────────────
# READ HELPERS
# ─────────────────────────────────────────
def read_mpu_raw(reg):
    data = i2c.readfrom_mem(MPU, reg, 2)
    val = (data[0] << 8) | data[1]
    if val > 32767:
        val -= 65536
    return val

def read_qmc_raw(reg):
    data = i2c.readfrom_mem(QMC, reg, 2)
    val = (data[1] << 8) | data[0]  # little-endian
    if val > 32767:
        val -= 65536
    return val

def read_mpu():
    ax = read_mpu_raw(0x3B) / 16384.0   # g
    ay = read_mpu_raw(0x3D) / 16384.0
    az = read_mpu_raw(0x3F) / 16384.0
    gx = read_mpu_raw(0x43) / 131.0     # deg/s
    gy = read_mpu_raw(0x45) / 131.0
    gz = read_mpu_raw(0x47) / 131.0
    return ax, ay, az, gx, gy, gz

def read_qmc():
    mx = read_qmc_raw(0x00)
    my = read_qmc_raw(0x02)
    mz = read_qmc_raw(0x04)
    return mx, my, mz

# ─────────────────────────────────────────
# COMPLEMENTARY FILTER
# Blends accelerometer + gyroscope
# Alpha = how much we trust gyroscope (0.95 = 95%)
# ─────────────────────────────────────────
ALPHA = 0.95   # trust gyro more for fast movements
dt    = 0.05   # 50ms loop = 20Hz

# Fused angles (start at 0)
pitch = 0.0
roll  = 0.0

def complementary_filter(ax, ay, az, gx, gy, pitch, roll, dt):
    # Angle from accelerometer
    accel_pitch = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 180 / math.pi
    accel_roll  = math.atan2(-ax, az) * 180 / math.pi

    # Blend with gyroscope
    pitch = ALPHA * (pitch + gx * dt) + (1 - ALPHA) * accel_pitch
    roll  = ALPHA * (roll  + gy * dt) + (1 - ALPHA) * accel_roll

    return pitch, roll

# ─────────────────────────────────────────
# HEADING FROM MAGNETOMETER
# Gives compass direction (0-360°)
# ─────────────────────────────────────────
def get_heading(mx, my):
    heading = math.atan2(my, mx) * 180 / math.pi
    if heading < 0:
        heading += 360
    return heading

# ─────────────────────────────────────────
# POSITION MAPPING
# Converts fused sensor values → position index
# This is what gets sent to your GUI!
# ─────────────────────────────────────────

# Calibration reference (set during calibration step)
ref_pitch   = None
ref_roll    = None
ref_heading = None

def calibrate(pitch, roll, heading):
    global ref_pitch, ref_roll, ref_heading
    ref_pitch   = pitch
    ref_roll    = roll
    ref_heading = heading
    print(f"✔ Calibrated! Origin set.")
    print(f"  ref_pitch={pitch:.1f}  ref_roll={roll:.1f}  ref_heading={heading:.1f}")

def get_position_index(pitch, roll, heading):
    if ref_pitch is None:
        return 0  # not calibrated yet

    # Delta from origin
    d_pitch   = pitch   - ref_pitch
    d_roll    = roll    - ref_roll
    d_heading = heading - ref_heading

    # Normalize heading delta
    if d_heading > 180:  d_heading -= 360
    if d_heading < -180: d_heading += 360

    # Combined movement score
    # Adjust SCALE to match your physical page size
    # Higher scale = more movement needed per character
    SCALE = 5.0
    position = int((d_pitch + d_roll * 0.5 + d_heading * 0.3) / SCALE)

    # Clamp to positive values only
    position = max(0, position)
    return position

# ─────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────
init_sensors()
time.sleep(0.5)

print("\n=== Braill'ie Sensor Fusion ===")
print("Press CTRL+C then type: calibrate() to set origin\n")

# Auto-calibrate on start after 2 seconds
print("Auto-calibrating in 2 seconds... hold glove at top-left of page!")
time.sleep(2)

loop_count = 0

while True:
    # Read sensors
    ax, ay, az, gx, gy, gz = read_mpu()
    mx, my, mz             = read_qmc()

    # Fuse accel + gyro
    pitch, roll = complementary_filter(ax, ay, az, gx, gy, pitch, roll, dt)

    # Get heading from compass
    heading = get_heading(mx, my)

    # Auto calibrate on first reading
    if loop_count == 0:
        calibrate(pitch, roll, heading)

    # Get position index
    pos = get_position_index(pitch, roll, heading)

    # Print every reading
    print(f"pitch={pitch:6.1f}°  roll={roll:6.1f}°  heading={heading:6.1f}°  → position={pos}")

    loop_count += 1
    time.sleep(dt)
