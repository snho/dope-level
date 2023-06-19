import time
import math
import terminalio
import board
import busio
import neopixel
import displayio
import digitalio
import adafruit_max1704x
import adafruit_uc8151d
from adafruit_debouncer import Button
from adafruit_display_text import label
from adafruit_bme280 import basic as adafruit_bme280
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
spi = board.SPI()  # Uses SCK and MISO/MOSI pins on board

# Setup EPD Pins
epd_dc = board.D10
epd_cs = board.D11
epd_reset = board.D12
epd_busy = board.D13

# Setup sensors
bno = BNO08X_UART(uart)
bme = adafruit_bme280.Adafruit_BME280_I2C(i2c)
bat = adafruit_max1704x.MAX17048(i2c)

# Setup LEDs
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

# Setup buttons
def make_button(pin):
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    return lambda: button.value

button_select = Button(make_button(board.A0))
button_up = Button(make_button(board.A1))
button_down = Button(make_button(board.A2))
button_left = Button(make_button(board.A3))
button_right = Button(make_button(board.A4))

# Check Button State - run this often
def update_buttons():
    button_select.update()
    button_up.update()
    button_down.update()
    button_left.update()
    button_right.update()

# Enable IMU
bno.enable_feature(BNO_REPORT_ACCELEROMETER)
bno.enable_feature(BNO_REPORT_GYROSCOPE)
bno.enable_feature(BNO_REPORT_MAGNETOMETER)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

# Setup sea-level
bme.sea_level_pressure = 1013.25

# Set text, front, colour
font = terminalio.FONT
white = 0xFFFFFF
black = 0x000000
red = 0xFF0000

# EPD Display Dimensions
EPD_HEIGHT = 296
EPD_WIDTH = 128

# Setup EPD Display Bus 
display_epd_bus = displayio.FourWire(spi, command=epd_dc, chip_select=epd_cs, reset=epd_reset, baudrate=1000000)

print("Display bus setup")
time.sleep(1)  # Wait a bit
print("sleep")

# Create EPD display object - the third color is red (0xff0000)
display_epd = adafruit_uc8151d.UC8151D(
    display_epd_bus,
    width=EPD_WIDTH,
    height=EPD_HEIGHT,
    rotation=180,
    busy_pin=epd_busy,
    highlight_color=0xFF0000,
)

# Create TFT display object
display_tft = board.DISPLAY

# TFT Display Groups
display_group_imu = displayio.Group(scale=2)
display_group_battery = displayio.Group(scale=2)
display_group_enviro = displayio.Group(scale=2)

display_group_menu = displayio.Group(scale=2)

# EPD Display Groups
epd_group_dope = displayio.Group()
epd_group_cartridge = displayio.Group()
epd_group_dope_table = displayio.Group(scale=2)

# Set a background
background_bitmap = displayio.Bitmap(EPD_WIDTH, EPD_HEIGHT, 1)
# Map colours in a palette
palette = displayio.Palette(1)
palette[0] = white

# Create a Tilegrid for white background on the EPD
epd_background = displayio.TileGrid(background_bitmap, pixel_shader=palette)
epd_group_dope.append(epd_background)

# Display Group Offsets
display_group_imu.x = 10
display_group_imu.y = 20

display_group_menu.x = 10
display_group_enviro.x = 20

epd_group_dope_table.x = 0
epd_group_dope_table.y = 25

# Merging groups to their respective main displays
epd_group_dope.append(epd_group_cartridge)
epd_group_dope.append(epd_group_dope_table)

# Setup TFT Labels
batt_percent_label = label.Label(font, text="", color=white, x=0, y=5)
batt_voltage_label = label.Label(font, text="", color=white, x=0, y=15)
batt_charge_rate_label = label.Label(font, text="", color=white, x=0, y=25)
accel_raw_label = label.Label(font, text="", color=white, x=0, y=5)
compass_label = label.Label(font, text="", color=white, x=0, y=35)
temperature_label = label.Label(font, text="", color=white,x=0, y=5)
humidity_label = label.Label(font, text="", color=white, x=0,y=15)
pressure_label = label.Label(font, text="", color=white, x=0, y=25)

# EPD Labels
cartridge_label = label.Label(font, text="22LR CCI SV 40GR", color=black, x=0, y=5)
range_label = label.Label(font, text="75m\r\n100m\r\n125m\r\n150m\r\n175m\r\n200m\r\n225m\r\n250m\r\n275m", color=black, x=0, y=0)
drop_table_label = label.Label(font, text="U1.0\r\nU2.3\r\nU3.7\r\nU5.2\r\nU6.8\r\nU8.5\r\nU10.3\r\nU12.2\r\nU14.1", color=black, x= 35, y=0)

# EPD Load Lists
cartridge_types = ["22LR CCI SV 40GR", "22LR AGUILA SV 40GR", "22LR REM GB 36GR"]
cartridge_types_index = 0

drop_table = ["U1.0\r\nU2.3\r\nU3.7\r\nU5.2\r\nU6.8\r\nU8.5\r\nU10.3\r\nU12.2\r\nU14.1", "U0.8\r\nU1.9\r\nU3.0\r\nU4.2\r\nU5.5\r\nU6.8\r\nU8.2\r\nU9.7\r\nU11.2", "U0.7\r\nU1.6\r\nU2.6\r\nU3.8\r\nU5.0\r\nU6.3\r\nU7.6\r\nU9.1\r\nU10.6"]
drop_table_index = 0

# Append Labels to Display Groups
display_group_battery.append(batt_percent_label)
display_group_battery.append(batt_voltage_label)
display_group_battery.append(batt_charge_rate_label)

display_group_imu.append(accel_raw_label)
display_group_imu.append(compass_label)

display_group_enviro.append(temperature_label)
display_group_enviro.append(humidity_label)
display_group_enviro.append(pressure_label)

epd_group_cartridge.append(cartridge_label)
epd_group_dope_table.append(range_label)
epd_group_dope_table.append(drop_table_label)

# Battery Display
def display_update_battery():   
    batt_percent_label.text = "REMAINING: {:.1f}%".format(bat.cell_percent)
    batt_voltage_label.text = "BATT. VOLT: {:.2f}V".format(bat.cell_voltage)
    batt_charge_rate_label.text = "(DIS)CHARGE RATE: {:.1f}%/hr".format(bat.charge_rate)

# Gyro Display
def display_update_gyro():
    accel_x, accel_y, accel_z = bno.acceleration

    accel_raw_label.text = "X: %0.3f  Y: %0.3f Z: %0.3f  m/s^2" % (accel_x, accel_y, accel_z)

# Compass Display
def display_update_compass():
    mag_x, mag_y, mag_z = bno.magnetic

    compass_bearing = (180 / 3.14) * math.atan2(mag_y, mag_x)

    if compass_bearing < 0:
        compass_bearing += 360
    
    compass_label.text = "COMPASS\r\n{:.0f} *M".format(compass_bearing)

# Environmental Display
def display_update_bme():
    temperature_label.text = "TEMP: {:.1f} C".format(bme.temperature)
    humidity_label.text = "HUMI: {:.1f} %".format(bme.humidity)
    pressure_label.text = "PRES: {:.1f} hPa".format(bme.pressure)

# EPD Start Time
epd_last_refreshed = -180.0

print("EPD TIME DONE")
# Setup Menu Labels
main_menu_items = ["LEVEL", "DOPE TABLE", "ENVIRONMENTAL", "BATTERY"]
main_menu_index = 0
main_menu_labels = []

print("main menu statics done")
for i, item in enumerate(main_menu_items):
    print("setting up main menu labels")
    menu_label = label.Label(font, padding_left=1,text=item, color=0xFFFFFF, x=0, y= 5 + i * 15)
    main_menu_labels.append(menu_label)
    display_group_menu.append(menu_label)

print("About to start the loop")
display_tft.show(display_group_menu)

while True:
    update_buttons()

    if button_select.pressed:
        print("Board Button Pressed")

    if button_up.pressed:
        print("Up Button Pressed")
        main_menu_index -= 1
        if main_menu_index < 0:
            main_menu_index = len(main_menu_items) - 1
        elif button_down.pressed:
            main_menu_index += 1
        if main_menu_index >= len(main_menu_items):
            main_menu_index = 0
    
    if button_down.pressed:
        print("Down Button Pressed")
        main_menu_index += 1
        if main_menu_index >= len(main_menu_items):
            main_menu_index = 0
    
    # Update display with selected menu item
    for i, label in enumerate(main_menu_labels):
        if i == main_menu_index:
            label.color = 0x000000  # Highlight selected item
            label.background_color = 0xFFFFFF
        else:
            label.color = 0xFFFFFF
            label.background_color = 0x000000

    if button_right.pressed:
        print("Right Button Pressed")
        selected_item = main_menu_items[main_menu_index]
        print("Selected item:", selected_item)
        if main_menu_index == 0:
            display_tft.show(display_group_imu)
        if main_menu_index == 1:
            print("SHOW DOPE SD")
            # TODO: SD CARD LIST FILES
            select_pressed = time.monotonic()
            if select_pressed > epd_last_refreshed + 180.0:
                print("Safe to update screen")
                cartridge_types_index = (cartridge_types_index + 1) % len(cartridge_types)
                drop_table_index = (drop_table_index + 1) % len(drop_table)
                cartridge_label.text = cartridge_types[cartridge_types_index]
                drop_table_label.text = drop_table[drop_table_index]
                epd_last_refreshed = time.monotonic()
                display_epd.show(epd_group_dope)
                display_epd.refresh()
            else:
                print("EPD refreshed too early!")
        if main_menu_index == 2:
            display_tft.show(display_group_enviro)
        if main_menu_index == 3:
            display_tft.show(display_group_battery)

    if button_left.pressed:
        print("Left Button Pressed")
        display_tft.show(display_group_menu)

    update_buttons()
    display_update_battery()
    display_update_gyro()
    update_buttons()
    display_update_compass()
    display_update_bme()
