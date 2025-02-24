""" Implements AF timer controls for the Federal Signal 3T22A. """

from gpiozero import LED
from siren import Motor, Siren, Solenoid

class FS3T22A(Siren):
    def __init__(self, motor_gpio, high_gpio, low_gpio, lock, cond):
        super(FS3T22A, self).__init__(lock, cond)
        self._motor = Motor(LED(motor_gpio))
        self._top_sol = Solenoid(LED(high_gpio))
        self._bottom_sol = Solenoid(LED(low_gpio))

    def _on_test(self):
        self._on_alert()

    def _on_alert(self):
        self._motor.on()
        self._wait_for_cancel()
        self._off()

    def _on_fire(self):
        self._motor.on()
        while True:
            self._top_sol.off()
            self._bottom_sol.on()
            if self._wait_for_cancel(0.5):
                break
            self._bottom_sol.off()
            self._top_sol.on()
            if self._wait_for_cancel(0.5):
                break
        self._off()

    def _on_attack(self):
        while True:
            self._motor.on()
            self._wait_for_cancel(4)
            self._motor.off()
            self._wait_for_cancel(4)
        self._off()

    def _off(self):
        self._motor.off()
        self._top_sol.off()
        self._bottom_sol.off()
