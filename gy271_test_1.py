# GY-271 (QMC5883L) Sensor Test
# Should print X, Y, Z magnetic field values
# If values change when you rotate the sensor = working!

from machine import I2C, Pin
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

QMC = 0x0D

# Initialize QMC5883L
i2c.writeto_mem(QMC, 0x0B, b'\x01')  # Set/Reset period
i2c.writeto_mem(QMC, 0x09, b'\x1D')  # Continuous mode, 200Hz, 8G, 512 OSR

print("GY-271 (QMC5883L) Test Started!")
print("Rotate the sensor and watch values change...\n")

def read_raw(reg):
    data = i2c.readfrom_mem(QMC, reg, 2)
    val = (data[1] << 8) | data[0]  # little-endian
    if val > 32767:
        val -= 65536
    return val

while True:
    # Check data ready flag
    status = i2c.readfrom_mem(QMC, 0x06, 1)[0]
    if status & 0x01:
        x = read_raw(0x00)
        y = read_raw(0x02)
        z = read_raw(0x04)
        print(f"X: {x:6d}  |  Y: {y:6d}  |  Z: {z:6d}")
    time.sleep(0.3)
