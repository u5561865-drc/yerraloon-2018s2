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

    combStr = str(datetime.datetime.now().time())[0:11] + ',\t' + GyrStr + ',\t' + AccStr + ',\t' + DirStr + ',\t' + TemStr + '\n'

    buffer.append(combStr)

    return (buffer, (bufferIndex+1))

# flush
def flushBuffer(buffer, bufferIndex, file):
    gpio.output(IMU_LED, 0)
    for line in buffer:
        file.write(line)
        gpio.output(IMU_LED, 1)
        file.flush()
        gpio.output(IMU_LED, 0)
    return ([], 0)

# init
def init(bno, file, gpio):
    # Raspberry Pi configuration with serial UART and RST connected to GPIO 18:
    bno = BNO055.BNO055(serial_port='/dev/ttyAMA0', rst=18)#, gpio=gpio)

    if not bno.begin():
        raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

    # Create the logging file
    refTime = str(datetime.datetime.now().time())[0:11]
    filename = "/home/pi/IMU/log_imu_" + refTime  + ".csv"
    file = open(filename, "a")
    if os.stat(filename).st_size == 0:
        file.write("Timestamp,\tGyro_x,\tGyro_y,\tGyro_z,\tAcc_x,\tAcc_y,\tAcc_z,\tOrie_x,\tOrie_y,\tOrie_z,\tOrie_w,\tTemp_C\n")
        print('IMU logging file created')
    print('IMU logging file opened')
    
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

    # Flash LED twice when initialisation is complete
    gpio.output(IMU_LED, 1)
    time.sleep(0.1)
    gpio.output(IMU_LED, 0)
    time.sleep(0.1)
    gpio.output(IMU_LED, 1)
    time.sleep(0.1)
    gpio.output(IMU_LED, 0)
    
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
    IMU_Pressed = False
    IMU_Enabled = False
    IMU_Prev = False
    IMU_Curr = False

    buffer = []
    bufferSize = 100
    bufferIndex = 0

    try:
        while True:
            IMU_Prev = IMU_Enabled
            IMU_Curr = not gpio.input(IMU_Button)

            if IMU_Pressed and not IMU_Curr:
                IMU_Pressed = False
            elif not IMU_Pressed and IMU_Curr:
                IMU_Pressed = True
                IMU_Enabled = not IMU_Enabled

            if IMU_Enabled:
                gpio.output(IMU_LED, 1)
                (buffer, bufferIndex) = readFromIMU(bno, buffer, bufferIndex)
                if bufferIndex == bufferSize:
                    (buffer, bufferIndex) = flushBuffer(buffer, bufferIndex, file)
            elif not IMU_Enabled and IMU_Prev:
                gpio.output(IMU_LED, 0)
                (buffer, bufferIndex) = flushBuffer(buffer, bufferIndex, file)
            else:
                gpio.output(IMU_LED, 0)
    except Exception as e:
        print(e)
        failstate()

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