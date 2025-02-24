""" AF Timer implementation and configuration. """

# This timer supports sirens with a single motor and up to two
# solenoids.  Timers may or may not use this, but the pins arw
# wired regardless.  Chsnge these to fit your particular
# wiring.
MOTOR_GPIO = 26
HIGH_SOLENOID_GPIO = 20
LOW_SOLENOID_GPIO = 21

# Button GPIOs.
TEST_BUTTON_GPIO = 23
ALERT_BUTTON_GPIO = 22
FIRE_BUTTON_GPIO = 27
ATTACK_BUTTON_GPIO = 18
CANCEL_BUTTON_GPIO = 17

# LED GPIOs.
READY_LED_GPIO = 9
ALERT_LED_GPIO = 11