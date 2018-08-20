# imports
import logging
import sys
import time
import os
import datetime
import RPi.GPIO as rpi_GPIO
import Adafruit_GPIO as GPIO
from Adafruit_BNO055 import BNO055

# imports
import logging
import sys
import time
import os
import datetime
import RPi.GPIO as rpi_GPIO
import Adafruit_GPIO as GPIO
from Adafruit_BNO055 import BNO055

# pin decs
IMU_LED = 6 #BCM
IMU_Button = 5 #BCM

def readFromIMU(bno, buffer, bufferIndex):
    gx, gy, gz = bno.read_gyroscope()
    GyrStr = '{0:0.3F},\t{1:0.3F},\t{2:0.3F}'.format(
          gx, gy, gz)
    # Linear acceleration data (i.e. acceleration from movement, not gravity--
    # returned in meters per second squared):
    ax, ay, az = bno.read_linear_acceleration()
    AccStr = '{0:0.3F},\t{1:0.3F},\t{2:0.3F}'.format(
          ax, ay, az)
    # Orientation as a quaternion:
    dx, dy, dz, w = bno.read_quaternion()
    DirStr = '{0:0.3F},\t{1:0.3F},\t{2:0.3F},\t{3:0.3F}'.format(
          dx, dy, dz, w)
    # Sensor temperature in degrees Celsius:
    temp_c = bno.read_temp()
    TemStr = '{0:0.2F}'.format(
          temp_c)

    combStr = str(datetime.datetime.now().time())[0:11] + ',\t' + GyrStr + \
                  ',\t' + AccStr + ',\t' + DirStr + ',\t' + TemStr + '\n'
    print(combStr)
    buffer.append(combStr)

    return (buffer, (bufferIndex+1))

# init
def init(bno, file, gpio):
    # Raspberry Pi configuration with serial UART and RST connected to GPIO 18:
    bno = BNO055.BNO055(serial_port='/dev/ttyAMA0', rst=18)#, gpio=gpio)

    if not bno.begin():
        raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')
    
    # Print system status and self test result.
    status, self_test, error = bno.get_system_status()
    print('System status: {0}'.format(status))
    print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
    # Print out an error if system status is in error mode.
    if status == 0x01:
        print('System error: {0}'.format(error))
        print('See datasheet section 4.3.59 for the meaning.')

    # Print the calibration status, 0=uncalibrated and 3=fully calibrated.
    s, g, a, m = bno.get_calibration_status()
    print('Sys_cal={0} Gyro_cal={1} Accel_cal={2} Mag_cal={3}\n'.format(
          s, g, a, m))

    gpio.setup(IMU_LED, GPIO.OUT)
    gpio.set_high(IMU_LED)
    gpio.setup(IMU_Button, GPIO.IN, GPIO.PUD_UP)    
    return (bno, file, gpio)

# If something fails flash SOS in morse
def failstate():
    gpio.output(IMU_LED, 1)
    time.sleep(1)
    print("S")
    gpio.output(IMU_LED, 0)
    time.sleep(0.3)
    gpio.output(IMU_LED, 1)
    time.sleep(0.5)
    print("O")
    gpio.output(IMU_LED, 0)
    time.sleep(0.3)
    gpio.output(IMU_LED, 1)
    time.sleep(1)
    print("S")
    gpio.output(IMU_LED, 0)

# core
def core(bno, file, gpio):
     try:
        while True:
 

# main
if __name__ == '__main__':     # Program start from here
    try:
        try:
            bno = None
            file = None
            gpio = GPIO.get_platform_gpio(mode=rpi_GPIO.BCM)
            (bno, file, gpio) = init(bno, file, gpio)
            core(bno, file, gpio)
        except Exception as e:
            print(e)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be executed
        exit()