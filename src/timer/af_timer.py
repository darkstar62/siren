""" Implementation of the AF timer. """

from config import *
import gpiozero
import functools
import threading

class Mode:
    IDLE = 0
    TEST = 1
    ALERT = 2
    FIRE = 3
    ATTACK = 4
    FIRE_ATTACK = 5


class Button:
    TEST = 0
    ALERT = 1
    FIRE = 2
    ATTACK = 3
    CANCEL = 4


class AFTimer:
    def __init__(self, siren_cls):
        self._mode = Mode.IDLE

        self._led_alarm = gpiozero.LED(ALERT_LED_GPIO)
        self._led_ready = gpiozero.LED(READY_LED_GPIO)

        self._test_button = gpiozero.Button(TEST_BUTTON_GPIO)
        self._test_button.pin.bounce = 0.05
        self._test_button.when_pressed = functools.partial(self._button_pressed, Button.TEST)
        self._test_button.when_released = functools.partial(self._button_released, Button.TEST)

        self._alert_button = gpiozero.Button(ALERT_BUTTON_GPIO)
        self._alert_button.pin.bounce = 0.05
        self._alert_button.when_pressed = functools.partial(self._button_pressed, Button.ALERT)
        self._alert_button.when_released = functools.partial(self._button_released, Button.ALERT)

        self._fire_button = gpiozero.Button(FIRE_BUTTON_GPIO)
        self._fire_button.pin.bounce = 0.05
        self._fire_button.when_pressed = functools.partial(self._button_pressed, Button.FIRE)
        self._fire_button.when_released = functools.partial(self._button_released, Button.FIRE)

        self._attack_button = gpiozero.Button(ATTACK_BUTTON_GPIO)
        self._attack_button.pin.bounce = 0.05
        self._attack_button.when_pressed = functools.partial(self._button_pressed, Button.ATTACK)
        self._attack_button.when_released = functools.partial(self._button_released, Button.ATTACK)

        self._cancel_button = gpiozero.Button(CANCEL_BUTTON_GPIO)
        self._cancel_button.pin.bounce = 0.05
        self._cancel_button.when_pressed = functools.partial(self._button_pressed, Button.CANCEL)
        self._cancel_button.when_released = functools.partial(self._button_released, Button.CANCEL)

        self._thread = None
        self._cancel_lock = threading.Lock()
        self._cancel_cond = threading.Condition(self._cancel_lock)

        self._button_push_lock = threading.Lock()

        self._siren = siren_cls(
                MOTOR_GPIO,
                HIGH_SOLENOID_GPIO,
                LOW_SOLENOID_GPIO,
                self._cancel_lock,
                self._cancel_cond)

        self._led_ready.on()
        self._led_alarm.off()

    def _button_released(self, button):
        self._button_push_lock.acquire()
        if self._mode == Mode.TEST or (
                self._mode == Mode.IDLE and self._cancel_button.is_pressed):
            if button == Button.ALERT:
                self._siren._set_damper_low(False)
            elif button == Button.FIRE:
                self._siren._set_damper_high(False)
            elif button == Button.TEST:
                self.change_mode(Mode.IDLE)
        elif button == Button.CANCEL:
            self.change_mode(Mode.IDLE)
        self._button_push_lock.release()

    def _button_pressed(self, button):
        """ Called whenever a button push event is called.

        This can be called from multiple threads, and so needs to be thread-safe.
        """
        # Take the lock so we ensure we're only processing one mode change at a time.
        self._button_push_lock.acquire()

        # Figure out what combination of buttons is pushed, and switch to the appropriate mode.
        #
        # The combinations are as follows:
        #
        #  - Test: When pressed, activate siren test.  Turns off when released.
        #  - Alert: When pressed, activate siren alert mode.  Remains on when released.
        #  - Fire: When pressed, activate siren fire mode.  Remains on when released.
        #  - Attack: When pressed, activate siren attack mode.  Remains on when released.
        #  - Test + Alert: When pressed, activate siren test, and actuate low damper.
        #        Damper opens when Alert released; siren turns off when Test released.
        #  - Test + Fire: When pressed, activate siren test, and actuate high damper.
        #        Damper opens when Fire released; siren turns off when Test released.
        #  - Alert + Fire: When pressed, activate fire alert mode.  Remains on when released.
        #  - Cancel: Turn off all remain-on modes and move to idle.
        if (self._mode == Mode.TEST and self._test_button.is_pressed) or (
                self._mode == Mode.IDLE and self._cancel_button.is_pressed):
            # Two additional buttons are allowed, and don't change modes, but do change what
            # the siren does.
            if button == Button.ALERT:
                self._siren._set_damper_low(True)
            elif button == Button.FIRE:
                self._siren._set_damper_high(True)

        elif self._mode == Mode.ATTACK and self._attack_button.is_pressed:
            if button == Button.FIRE:
                self.change_mode(Mode.FIRE_ATTACK)

        elif self._mode == Mode.FIRE and self._fire_button.is_pressed:
            if button == Button.ATTACK:
                self.change_mode(Mode.FIRE_ATTACK)

        elif self._mode == Mode.ALERT and self._alert_button.is_pressed:
            pass
        elif self._mode == Mode.FIRE_ATTACK and self._fire_button.is_pressed and self._attack_button.is_pressed:
            pass
        else:
            # From here, we got a single button push, meaning there's a first-level mode switch.
            if button == Button.TEST:
                self.change_mode(Mode.TEST)
            elif button == Button.ALERT:
                self.change_mode(Mode.ALERT)
            elif button == Button.FIRE:
                self.change_mode(Mode.FIRE)
            elif button == Button.ATTACK:
                self.change_mode(Mode.ATTACK)
            elif button == Button.CANCEL:
                self.change_mode(Mode.IDLE)

        self._button_push_lock.release()

    def _run_in_thread(self, callable):
        self.cancel()

        def wrapper():
            self._led_alarm.on()
            callable()
            self._led_alarm.off()

        print("Run in thread: %s", callable.__repr__())
        self._thread = threading.Thread(target=wrapper)
        self._thread.start()

    def change_mode(self, mode):
        """ Change to the specified mode, actuating the siren accordingly. """
        print("Change mode: ", mode, " from ", self._mode)
        if mode == Mode.IDLE:
            self.cancel()
        elif mode == Mode.ALERT:
            self.alert()
        elif mode == Mode.FIRE:
            self.fire()
        elif mode == Mode.FIRE_ATTACK:
            self.fire_attack()
        elif mode == Mode.ATTACK:
            self.attack()
        elif mode == Mode.TEST:
            self.test()
        else:
            print("Invalid mode: ", mode)
        print("Mode now ", self._mode)

    def test(self):
        self._run_in_thread(self._siren._on_test)
        self._mode = Mode.TEST

    def alert(self):
        self._run_in_thread(self._siren._on_alert)
        self._mode = Mode.ALERT

    def fire(self):
        self._run_in_thread(self._siren._on_fire)
        self._mode = Mode.FIRE

    def attack(self):
        self._run_in_thread(self._siren._on_attack)
        self._mode = Mode.ATTACK

    def fire_attack(self):
        self._run_in_thread(self._siren._on_fire_attack)
        self._mode = Mode.FIRE_ATTACK

    def cancel(self):
        with self._cancel_lock:
            print("Cancelling")
            self._cancel_cond.notify_all()

        if self._thread is not None:
            self._thread.join()
            print("cancelled")
            self._thread = None
        self._mode = Mode.IDLE
