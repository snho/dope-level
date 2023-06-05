import time
import math
import terminalio
import board
import busio
import displayio
import adafruit_max1704x
from adafruit_display_text import label
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.uart import BNO08X_UART

# Setup Buses
uart = busio.UART(board.TX, board.RX, baudrate=3000000, receiver_buffer_size=2048)
i2c = board.I2C()

# Setup sensors
bno = BNO08X_UART(uart)
bat = adafruit_max1704x.MAX17048(i2c)

# Enable IMU
bno.enable_feature(BNO_REPORT_ACCELEROMETER)
bno.enable_feature(BNO_REPORT_GYROSCOPE)
bno.enable_feature(BNO_REPORT_MAGNETOMETER)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

# Battery
def print_battery():
    print(f"Battery voltage = {bat.cell_voltage:.2f}V")
    print(f"Battery remaining: {bat.cell_percent:.1f}%")

# Acceleration
def print_accel():
    print("Acceleration:")
    accel_x, accel_y, accel_z = bno.acceleration
    print("X: %0.6f  Y: %0.6f Z: %0.6f  m/s^2" % (accel_x, accel_y, accel_z))
    print("")
    
# Gyro 
def print_gyro():
    print("Gyro:")
    gyro_x, gyro_y, gyro_z = bno.gyro
    print("X: %0.6f  Y: %0.6f Z: %0.6f rads/s" % (gyro_x, gyro_y, gyro_z))
    print("")

# Magnetometer
def print_mag():
    print("Magnetometer:")
    mag_x, mag_y, mag_z = bno.magnetic
    print("X: %0.6f  Y: %0.6f Z: %0.6f uT" % (mag_x, mag_y, mag_z))
    print("")

# Rotation Vector
def print_vect_quat():
    print("Rotation Vector Quaternion:")
    quat_i, quat_j, quat_k, quat_real = bno.quaternion
    print(
        "I: %0.6f  J: %0.6f K: %0.6f  Real: %0.6f" % (quat_i, quat_j, quat_k, quat_real)
    )
    print("")

# Setup Onboard Display
display_tft = board.DISPLAY

# Set text, front, colour
font = terminalio.FONT
white = 0xFFFFFF

# Display Group Battery
display_group_diag = displayio.Group()
display_group_battery = displayio.Group()
display_group_imu = displayio.Group()

# Display Group Offsets
display_group_imu.x = 0
display_group_imu.y = 35

# Display Groups
display_group_diag.append(display_group_battery)
display_group_diag.append(display_group_imu)

# Setup Text Labels
batt_percent_label = label.Label(font, text="BATTERY REMAINING: {:.1f}%".format(bat.cell_percent), color=white, x=0, y=5)
batt_voltage_label = label.Label(font, text="BATTERY VOLTAGE: {:.2f}V".format(bat.cell_voltage), color=white, x=0, y=15)
batt_charge_rate_label = label.Label(font, text="BATTERY (DIS)CHARGE RATE: {:.2f}%/hr".format(bat.charge_rate), color=white, x=0, y=25)
gyro_raw_label = label.Label(font, text="GYRO\r\nX: ----  Y: ---- Z: ---- rads/s", color=white, x=0, y=5)
compass_label = label.Label(font, text="COMPASS\r\n--- degrees", color=white, x=0, y=35)

# Append Labels to Display Groups
display_group_battery.append(batt_percent_label)
display_group_battery.append(batt_voltage_label)
display_group_battery.append(batt_charge_rate_label)
display_group_imu.append(gyro_raw_label)
display_group_imu.append(compass_label)

# Battery Display
def display_update_battery():   
    batt_percent_label.text = "BATTERY REMAINING: {:.1f}%".format(bat.cell_percent)
    batt_voltage_label.text = "BATTERY VOLTAGE: {:.2f}V".format(bat.cell_voltage)
    batt_charge_rate_label.text = "BATTERY (DIS)CHARGE RATE: {:.1f}%/hr".format(bat.charge_rate)

# Gyro Display
def display_update_gyro():
    gyro_x, gyro_y, gyro_z = bno.gyro

    gyro_raw_label.text = "GYRO\r\nX: %0.4f  Y: %0.4f Z: %0.4f rads/s" % (gyro_x, gyro_y, gyro_z)

def display_update_compass():
    mag_x, mag_y, mag_z = bno.magnetic

    compass_bearing = (180 / 3.14) * math.atan2(mag_y, mag_x)

    if compass_bearing < 0:
        compass_bearing += 360
    
    compass_label.text = "MAGNETIC COMPASS\r\n{:.0f} degrees".format(compass_bearing)

while True:
    display_update_battery()
    display_update_gyro()
    display_update_compass()
    # time.sleep(0.5) does not seem to crap out the UART
    display_tft.show(display_group_diag)
