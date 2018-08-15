#!/usr/bin/python

# This script outputs the data from the GPS module over serial

import sys
import time
import difflib
import pigpio

RX=23

EN=24

while True:
	try:
			pi = pigpio.pi()
			pi.set_mode(RX, pigpio.INPUT)
			pi.set_mode(EN, pigpio.OUTPUT)
			pi.write(EN,True)
			
			pi.bb_serial_read_open(RX, 9600, 8)

			while 1:
					(count, data) = pi.bb_serial_read(RX)
					if count:
							print count, data
					time.sleep(1)

	except:
			pi.bb_serial_read_close(RX)
			pi.stop()
