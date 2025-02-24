""" Implementation of the AF timer. """

from config import *
from gpiozero import Button, LED
import threading

class AFTimer:
    def __init__(self, siren_cls):
        self._led_alarm = LED(ALERT_LED_GPIO)
        self._led_ready = LED(READY_LED_GPIO)

        self._test_button = Button(TEST_BUTTON_GPIO)
        self._test_button.pin.bounce = 0.05
        self._test_button.when_pressed = self.test
        self._test_button.when_released = self.cancel

        self._alert_button = Button(ALERT_BUTTON_GPIO)
        self._alert_button.pin.bounce = 0.05
        self._alert_button.when_pressed = self.alert

        self._fire_button = Button(FIRE_BUTTON_GPIO)
        self._fire_button.pin.bounce = 0.05
        self._fire_button.when_pressed = self.fire

        self._attack_button = Button(ATTACK_BUTTON_GPIO)
        self._attack_button.pin.bounce = 0.05
        self._attack_button.when_pressed = self.attack

        self._cancel_button = Button(CANCEL_BUTTON_GPIO)
        self._cancel_button.pin.bounce = 0.05
        self._cancel_button.when_pressed = self.cancel

        self._thread = None
        self._cancel_lock = threading.Lock()
        self._cancel_cond = threading.Condition(self._cancel_lock)

        self._siren = siren_cls(
                MOTOR_GPIO,
                HIGH_SOLENOID_GPIO,
                LOW_SOLENOID_GPIO,
                srlf._cancel_lock,
                self._cancel_cond)

        self._led_ready.on()
        self._led_alarm.off()

    def _run_in_thread(self, callable):
        self.cancel()

        def wrapper():
            self._led_alarm.on()
            callable()
            self._led_alarm.off()

        self._thread = threading.Thread(target=wrapper)
        self._thread.start()

    def test(self):
        self._run_in_thread(self._siren._on_test)

    def alert(self):
        self._run_in_thread(self._siren._on_alert)

    def fire(self):
        self._run_in_thread(self._siren._on_fire)

    def attack(self):
        self._run_in_thread(self._siren._on_attack)

    def cancel(self):
        with self._cancel_lock:
            print("Cancelling")
            self._cancel_cond.notify_all()

        if self._thread is not None:
            self._thread.join()
            print("cancelled")
            self._thread = None
