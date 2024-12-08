import time
from machine import Pin
from tiny_fx import TinyFX

tiny = TinyFX()

pir = Pin(tiny.SENSOR_PIN, Pin.IN, Pin.PULL_UP)

try:
	while True:

		while not tiny.boot_pressed():

			# print("PIR value:", pir.value())

			if pir.value() == 0:
				print("Nothing...")

			if pir.value() == 1:
				print("Huzzah!")

			time.sleep(1)

except KeyboardInterrupt:
	tiny.shutdown()