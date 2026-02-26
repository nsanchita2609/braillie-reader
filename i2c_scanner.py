# I2C Scanner — Run this first!
# If sensors are wired correctly, you should see their addresses printed
# MPU6050 should appear as: 0x68
# GY-271 (QMC5883L) should appear as: 0x0D  or  HMC5883L as 0x1E

from machine import I2C, Pin

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

print("Scanning I2C bus...")
devices = i2c.scan()

if devices:
    print(f"Found {len(devices)} device(s):")
    for d in devices:
        print(f"  Address: 0x{d:02X}")
else:
    print("No devices found! Check your wiring.")

# What you should see:
# 0x68 = MPU6050 (accelerometer/gyro)
# 0x0D = GY-271 with QMC5883L chip
# 0x1E = GY-271 with HMC5883L chip
