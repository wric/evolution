import board
import busio
import digitalio
import RPi.GPIO as GPIO
from adafruit_max31865 import MAX31865


def sensor(pin):
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(getattr(board, f"D{pin}"))
    return MAX31865(spi, cs, wires=2)


def ssr(pin):
    GPIO.setup(pin, GPIO.OUT)
    ssr = GPIO.PWM(pin, 50)
    ssr.start(0)
    return ssr
