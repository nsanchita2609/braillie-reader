# MPU6050 Sensor Test
# Should print X, Y, Z acceleration values
# If values change when you tilt/move the sensor = working!

from machine import I2C, Pin
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

MPU = 0x68

# Wake up MPU6050 (it starts in sleep mode)
i2c.writeto_mem(MPU, 0x6B, b'\x00')
print("MPU6050 Test Started!")
print("Move/tilt the sensor and watch values change...\n")

def read_raw(reg):
    data = i2c.readfrom_mem(MPU, reg, 2)
    val = (data[0] << 8) | data[1]
    if val > 32767:
        val -= 65536
    return val

while True:
    ax = read_raw(0x3B) / 16384.0
    ay = read_raw(0x3D) / 16384.0
    az = read_raw(0x3F) / 16384.0

    print(f"X: {ax:.2f}g  |  Y: {ay:.2f}g  |  Z: {az:.2f}g")
    time.sleep(0.5)
