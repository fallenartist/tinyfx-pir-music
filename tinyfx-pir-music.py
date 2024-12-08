import time
import random
from machine import Pin
from tiny_fx import TinyFX

# Initialize TinyFX with the "wav" folder for audio
tiny = TinyFX(wav_root="/wav")

# Configure PIR sensor input pin (example: GP6)
# Adjust the pin number according to your actual wiring.
# If the PIR output is open-drain or requires a pull-up, adjust accordingly.
pir_pin = Pin(tiny.SENSOR_PIN, Pin.IN, Pin.PULL_UP)

try:
	while True:
		# Variables for timing
		last_rgb_flash_time = time.time()

		# Idle state:
		# Flash RGB LEDs every 4.8 seconds until PIR triggers or BOOT button is pressed
		while not tiny.boot_pressed() and pir_pin.value() == 1:
			current_time = time.time()
			# Check if it's time to update RGB LEDs
			if current_time - last_rgb_flash_time >= 4.8:
				# Set RGB LEDs to random color
				r = random.randint(0, 255)
				g = random.randint(0, 255)
				b = random.randint(0, 255)
				tiny.rgb.set_rgb(r, g, b)
				last_rgb_flash_time = current_time

			# Brief sleep to keep checking for triggers
			time.sleep(0.1)

		# Once triggered by either PIR or BOOT button:
		# Start playing the audio
		tiny.clear()

		# log

		tiny.wav.play_wav("jingle-bells-mono.wav")

		# Timing variables for playback
		last_rgb_flash_time = time.time()
		last_mono_led_time = time.time()

		# While audio is playing
		while tiny.wav.is_playing():
			current_time = time.time()

			# Flash RGB LEDs
			if current_time - last_rgb_flash_time >= 0.6:
				r = random.randint(0, 255)
				g = random.randint(0, 255)
				b = random.randint(0, 255)
				tiny.rgb.set_rgb(r, g, b)
				last_rgb_flash_time = current_time

			# Update mono LEDs
			if current_time - last_mono_led_time >= 1.2:
				last_mono_led_time = current_time
				for output in tiny.outputs:
					# Randomly turn on or off each output
					if random.choice([True, False]):
						output.on()
					else:
						output.off()

			# Brief sleep for loop responsiveness
			time.sleep(0.1)

		# After audio playback, turn off mono LEDs
		for output in tiny.outputs:
			output.off()

except KeyboardInterrupt:
	# Graceful shutdown on interrupt
	tiny.shutdown()