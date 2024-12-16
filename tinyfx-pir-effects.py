import time
import math
import random
from machine import Pin
from tiny_fx import TinyFX
from picofx import rgb_from_hsv

tiny = TinyFX(wav_root="/wav")
pir_pin = Pin(tiny.SENSOR_PIN, Pin.IN, Pin.PULL_UP)

STATE_IDLE = 0
STATE_TRIGGERED = 1
state = STATE_IDLE
PIR_CHECK_DELAY = 2.0
AUDIO_FILE = "jingle-bells-mono.wav"

# Pulsing random RGB LEDs
class PulsingHSVFX:
	def __init__(self, cycle_time=1.0, max_val=1.0, sat=1.0):
		self.cycle_time = cycle_time * 1000  # ms
		self.max_val = max_val
		self.sat = sat
		self.hue = random.random()
		self.time_in_cycle = 0

	def tick(self, delta_ms):
		self.time_in_cycle += delta_ms
		if self.time_in_cycle > self.cycle_time:
			self.time_in_cycle -= self.cycle_time
			self.hue = random.random()

	def get_rgb(self):
		# offset from 0 to 1
		offset = self.time_in_cycle / self.cycle_time
		# half sine wave 0->max->0
		angle = offset * math.pi
		val = math.sin(angle) * self.max_val
		r, g, b = rgb_from_hsv(self.hue, self.sat, val)
		return r, g, b

# Two sets of effects: idle and triggered
idle_fx = PulsingHSVFX(cycle_time=4.8, max_val=0.25)
triggered_fx = PulsingHSVFX(cycle_time=0.6, max_val=1.0)

# Random mono LEDs on-off
class RandomIntervalFX:
	def __init__(self, interval=1.2, brightness_min=0.0, brightness_max=1.0):
		self.interval = interval * 1000
		self.brightness_min = brightness_min
		self.brightness_max = brightness_max
		self.time_accum = 0
		self.value = random.uniform(brightness_min, brightness_max)

	def tick(self, delta_ms):
		self.time_accum += delta_ms
		if self.time_accum >= self.interval:
			self.time_accum -= self.interval
			self.value = random.uniform(self.brightness_min, self.brightness_max)

	def get_brightness(self):
		return self.value

# Apple effect to mono LEDs when triggered
triggered_mono = [RandomIntervalFX(interval=1.2, brightness_min=0.0, brightness_max=1.0) for _ in range(6)]

try:
	last_trigger_time = None
	last_time = time.ticks_ms()

	while not tiny.boot_pressed():
		now = time.ticks_ms()
		delta = time.ticks_diff(now, last_time)
		last_time = now

		pir_val = pir_pin.value()  # 1 = motion, 0 = no motion

		# Update effects based on state
		if state == STATE_IDLE:
			# Update idle FX
			idle_fx.tick(delta)
			r, g, b = idle_fx.get_rgb()

			# Apply RGB (0-1.0 brightness * 255)
			tiny.rgb.set_rgb(int(r*255), int(g*255), int(b*255))

			# Mono off
			for out in tiny.outputs:
				out.off()

			if pir_val == 1:
				# Motion detected
				if last_trigger_time is None:
					last_trigger_time = time.time()
				elif (time.time() - last_trigger_time) >= PIR_CHECK_DELAY:
					if pir_pin.value() == 1:
						# Trigger
						state = STATE_TRIGGERED
						tiny.wav.play_wav(AUDIO_FILE)
						# Reset triggered FX timing
						triggered_fx.time_in_cycle = 0
						for fx in triggered_mono:
							fx.time_accum = 0
						last_trigger_time = None
					else:
						last_trigger_time = None
			else:
				last_trigger_time = None

		elif state == STATE_TRIGGERED:
			# Update triggered FX
			triggered_fx.tick(delta)
			r, g, b = triggered_fx.get_rgb()
			tiny.rgb.set_rgb(int(r*255), int(g*255), int(b*255))

			# Update and apply mono random FX
			for i, fx in enumerate(triggered_mono):
				fx.tick(delta)
				brightness = fx.get_brightness()
				# Convert brightness to LED on/off using PWM or just scale brightness if available.
				# If outputs are just on/off, turn on if brightness > 0.5, off otherwise:
				# For simplicity, just use on/off:
				if brightness > 0.5:
					tiny.outputs[i].on()
				else:
					tiny.outputs[i].off()

			# Check if audio finished
			if not tiny.wav.is_playing():
				# Back to idle
				state = STATE_IDLE

		# No large sleep, just a small pause if needed
		time.sleep(0.01)

except KeyboardInterrupt:
	# Turn everything off
	tiny.shutdown()