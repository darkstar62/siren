""" Implements AF timer controls for the Federal Signal 3T22A. """

try:
    from gpiozero import LED
except:
    from test.fake_gpiozero import LED
from siren import Motor, Siren, Solenoid

class FS3T22A(Siren):
    """ Implements the various signalling modes for a Federal Signal 3T22A.

    This siren has a motor that controls two rotors, a high and a low.  It additionally
    has two independently addressable solenoid-controlled flaps on the intakes to allow
    for a high-low or muted operation.
    """

    def __init__(self, motor_gpio, high_gpio, low_gpio, lock, cond):
        super(FS3T22A, self).__init__(lock, cond)
        self._motor = Motor(LED(motor_gpio))
        self._top_sol = Solenoid(LED(high_gpio))
        self._bottom_sol = Solenoid(LED(low_gpio))

    def __repr__(self):
        return '<FS3T22A: Model Federal Signal 3T22A>'

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

    def _on_fire_attack(self):
        motor_next = True
        cancelled = False
        while not cancelled:
            if motor_next:
                self._motor.on()
                motor_next = False
            else:
                self._motor.off()
                motor_next = True

            for secs in range(4):
                self._top_sol.off()
                self._bottom_sol.on()
                if self._wait_for_cancel(0.5):
                    cancelled = True
                    break
                self._bottom_sol.off()
                self._top_sol.on()
                if self._wait_for_cancel(0.5):
                    cancelled = True
                    break
        self._off()

    def _on_attack(self):
        while True:
            self._motor.on()
            if self._wait_for_cancel(4):
                break
            self._motor.off()
            if self._wait_for_cancel(4):
                break
        self._off()

    def _set_damper_high(self, closed):
        if closed:
            self._top_sol.on()
        else:
            self._top_sol.off()

    def _set_damper_low(self, closed):
        if closed:
            self._bottom_sol.on()
        else:
            self._bottom_sol.off()

    def _off(self):
        self._motor.off()
        self._top_sol.off()
        self._bottom_sol.off()
