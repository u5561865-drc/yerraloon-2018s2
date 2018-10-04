# imports
import logging
import sys
import time
import os
import datetime
import math
import RPi.GPIO as rpi_GPIO
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.PWM as PWM
from Adafruit_BNO055 import BNO055

# pin decs
IMU_LED = 6 #BCM
IMU_Button = 5 #BCM

def readFromIMU(bno):    #, buffer, bufferIndex):
    gx, gy, gz = bno.read_gyroscope()
    # Linear acceleration data (i.e. acceleration from movement, not gravity--
    # returned in meters per second squared):
    ax, ay, az = bno.read_linear_acceleration()
    # Orientation as a quaternion:
    dx, dy, dz, w = bno.read_quaternion()
    return (gx, gy, gz, ax, ay, az, dx, dy, dz, w)

# init
def init(bno, gpio):
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

    # Flash LED twice when initialisation is complete
    gpio.output(IMU_LED, 1)
    time.sleep(0.1)
    gpio.output(IMU_LED, 0)
    time.sleep(0.1)
    gpio.output(IMU_LED, 1)
    time.sleep(0.1)
    gpio.output(IMU_LED, 0)
    
    return (bno, gpio)

def quaternionToEulerAngle(w, x, y, z):
    ysqr = y * y
    
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    X = math.degrees(math.atan2(t0, t1))
    
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))
    
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = math.degrees(math.atan2(t3, t4))
    return X, Y, Z

def yawFromQuatenion(w, x, y, z):
    ysqr = y * y
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = math.degrees(math.atan2(t3, t4))
    return Z    

# main
if __name__ == '__main__':     # Program start from here
    try:
        try:
            bno = None
            gpio = GPIO.get_platform_gpio(mode=rpi_GPIO.BCM)
            pwm = PWM.get_platform_pwm()
            (bno, gpio) = init(bno, gpio)

            dt = 0.1
            f = 1/dt 
                        
            # set up the relays
            relay1 = 12
            pwm.start(relay1, 0, f)
            relay2 = 18
            pwm.start(relay2, 0, f)

            #init control gains
            Ki = 1
            Kp = 1
            Kd = 1
            
            windup_guard = 20.0
            target_pos = 0.0
            set_point = 0.0
            feedback_value = 0.0
            last_error = 0.0
            last_time = time.time()
            I_term = 0.0

            while True: 
                #Get the current position   
                gx, gy, gz, ax, ay, az, dx, dy, dz, w = readFromIMU(bno)
                #Calculate the error 
                feedback_value = yawFromQuatenion(w, dx, dy, dz)
                error = set_point - feedback_value #or current_position
                #Calculate the derivative   
                delta_error = error - last_error
                
                current_time = time.time()
                delta_time = current_time - last_time 
                
                P_term = Kp * error 
                
                I_term += error * delta_time 

                if (I_term < windup_guard):
                    I_term = -windup_guard
                elif (I_term > windup_guard):
                    I_term = windup_guard    

                D_term = delta_error / delta_time 

                #Calculate the control variable 
                output = P_term + Ki * I_term + Kd * D_term  
                 
                #Calculate 
                last_time = time.time()
                last_error = error
                
                # calculate duty cycle
                kHW = 1
                dc = kHW * abs(output) / 100 #somthing like this... 

                if (output > 0):    
                    pwm.set_duty_cycle(relay2, dc)
                    pwm.set_duty_cycle(relay1, 0)
                elif (output <= 0):
                    pwm.set_duty_cycle(relay1, dc)
                    pwm.set_duty_cycle(relay2, 0)
            
        except Exception as e:
            print(e)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be executed
        exit()