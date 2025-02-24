""" Siren moduke for controlling warning sirens. """

# GPIO pin configuration
LED_READY = 9
LED_ALARM = 11

from .motor import Motor
from .siren import Siren
from .solenoid import Solenoid
