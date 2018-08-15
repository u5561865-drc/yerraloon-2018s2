#!/usr/bin/python

import sys
import time
import difflib
import pigpio
import pynmea2
import os
import datetime
from datetime import timedelta
import RPi.GPIO as GPIO

# Serial pins for GPS
RX = 23
EN = 24

# Pins for GPS button and LED
GPS_LED = 13
GPS_Button = 11

# Read data from the GPS
def readFromGPS(pi, excess, buffer, bufferIndex, timestampBuffer):
    (dataSize, data) = pi.bb_serial_read(RX)
    if dataSize > 0:
        allStr = excess + str(data)
        excess = ''
        senStartCount = allStr.count('$')

        # This section should probably be made more robust:
        # if the data is between 2 dollar signs is corrupted/missing it will 
        # still be appended to the buffer; if this happens a lot we can waste 
        # a lot of time unnecessarily flushing the buffer
        if senStartCount > 1: # contains a whole sentence
            sentStart = allStr.find('$')
            sentEnd = allStr[sentStart+1:].find('$') - 1
            excess = allStr[sentEnd+1:]
            sentence = allStr[sentStart:sentEnd]
            buffer.append(sentence)
            bufferIndex += 1
            sysTimestamp = str(datetime.datetime.now().time())[0:11]
            timestampBuffer.append(sysTimestamp)
        elif senStartCount == 1: # discard anything before start of sentence
            sentStart = allStr.find('$')
            excess = allStr[sentStart:]

    return (excess, buffer, bufferIndex, timestampBuffer)

# Clear out the buffer
def flushBuffer(buffer, bufferIndex, timestampBuffer):
    GPIO.output(GPS_LED, GPIO.LOW)
    tsbi = 0
    for sentence in buffer:
        print(sentence)
        try:
            msg = pynmea2.parse(sentence)
            try:
                GPSTime = str(msg.timestamp.strftime("%H:%M:%S"))
            except:
                GPSTime = '\t'
            write = timestampBuffer[tsbi] + ",\t" + GPSTime + ",\t" +  str(msg.latitude) + ",\t" + str(msg.longitude) + ",\t" + str(msg.altitude) + "\n"
            file.write(write)
            file.flush()

            # flash LED to indicate file is saving
            GPIO.output(GPS_LED, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(GPS_LED, GPIO.LOW)

            tsbi += 1
        except:
            print("unable to parse sentence: " + sentence)
            GPIO.output(GPS_LED, GPIO.LOW)
    
    GPIO.output(GPS_LED, GPIO.LOW)
    return ([], 0, [])

# Initialise the GPS module and prepare for file logging
def init(pi, file):
    # Initialize serial emulation library
    pi = pigpio.pi()
    pi.set_mode(RX, pigpio.INPUT)
    pi.set_mode(EN, pigpio.OUTPUT)
    pi.write(EN, True)
    try:
        pi.bb_serial_read_open(RX, 9600, 8)
    except Exception as e:
        pi.stop()
        raise ValueError(e)

    # Get a timestamp in order to differentiate from other log files (HH:MM:SS)
    refTime = str(datetime.datetime.now().time())[0:8]
    filename = "/home/pi/GPS/log_gps_" + refTime  + ".csv"
    
    # Open file for logging
    file = open(filename, "a")
    # Create file if not present
    if os.stat(filename).st_size == 0:
        file.write("System_Timestamp,\tGPS_Timestamp\tLatitude,\tLongitude,\tAltitude\n")

    GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
    GPIO.setup(GPS_LED, GPIO.OUT)   # Set GPS_LEDPin's mode to output
    GPIO.setup(GPS_Button, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set GPS_ButtonPin's mode as input

    # Flash LED twice when initialisation is complete
    GPIO.output(GPS_LED, 1)
    time.sleep(0.1)
    GPIO.output(GPS_LED, 0)
    time.sleep(0.1)
    GPIO.output(GPS_LED, 1)
    time.sleep(0.1)
    GPIO.output(GPS_LED, 0)
    
    return (pi, file)

# If something fails flash SOS in morse
def failstate():
    GPIO.output(GPS_LED, GPIO.HIGH)  # GPS LED on
    time.sleep(1)
    print("S")
    GPIO.output(GPS_LED, GPIO.LOW)   # GPS LED off
    
    time.sleep(0.3)
    
    GPIO.output(GPS_LED, GPIO.HIGH)  # GPS LED on
    time.sleep(0.5)
    print("O")
    GPIO.output(GPS_LED, GPIO.LOW)   # GPS LED off
    
    time.sleep(0.3)
    
    GPIO.output(GPS_LED, GPIO.HIGH)  # GPS LED on
    time.sleep(1)
    print("S")
    GPIO.output(GPS_LED, GPIO.LOW)   # GPS LED off

# clean up GPIO pins
def destroy():
    GPIO.output(GPS_LED, GPIO.LOW)   # GPS LED off
    GPIO.cleanup()                  # Release resource
    try:
        pi.stop()
    except:
        print("failed to stop pigpio")

# main logging loop
def core(pi, file):
    GPS_Pressed = False
    GPS_Enabled = False
    GPS_Prev = False
    GPS_Curr = False

    buffer = [] # buffer for separated sentences (in raw format)
    bufferSize = 60 # buffer size of 60 gives 1 minute of data when sensor is operating at 1 hz
    bufferIndex = 0 # position in buffer
    excess = '' # used for storing imcomplete sentences between cycles

    timestampBuffer = []

    try:
        # main loop
        while True:
            GPS_Prev = GPS_Enabled
            GPS_Curr = not GPIO.input(GPS_Button)

            # Toggle logging on and off with pushbutton
            if GPS_Pressed and not GPS_Curr:
                GPS_Pressed = False
                print('GPS Button Released')
            elif not GPS_Pressed and GPS_Curr:
                GPS_Pressed = True
                print('GPS Button Pressed')
                GPS_Enabled = not GPS_Enabled # Toggle GPS logging
            
            if GPS_Enabled:
                # Turn on LED, read data from GPS and flush buffer as required
                GPIO.output(GPS_LED, GPIO.HIGH)
                (excess, buffer, bufferIndex, timestampBuffer) = readFromGPS(pi, excess, buffer, bufferIndex, timestampBuffer)
                if bufferIndex == bufferSize:
                    (buffer, bufferIndex, timestampBuffer) = flushBuffer(buffer, bufferIndex, timestampBuffer)
            # gps has just been disabled, flush the buffer
            elif not GPS_Enabled and GPS_Prev:
                GPIO.output(GPS_LED, GPIO.LOW)
                (buffer, bufferIndex, timestampBuffer) = flushBuffer(buffer, bufferIndex, timestampBuffer)
            else:
                GPIO.output(GPS_LED, GPIO.LOW)

    except Exception as e:
        print(e)
        pi.bb_serial_read_close(RX)
        pi.stop()
        destroy()
        failstate()

if __name__ == '__main__':     # Program start from here
    try:
        try:
            pi = None
            file = None
            print("Initializing")
            (pi, file) = init(pi, file)
            print("initialisation complete\nEntering core")
            core(pi, file)
        except Exception as e:
            print(e)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be executed
        destroy()