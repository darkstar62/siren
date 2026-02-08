""" Implementation of the AF timer. """

try:
    from gpiozero import LED, Button as GPIOButton
except:
    from test.fake_gpiozero import LED, Button as GPIOButton
from config import *
import functools
import threading

class Mode:
    IDLE = 0
    TEST = 1
    ALERT = 2
    FIRE = 3
    ATTACK = 4
    FIRE_ATTACK = 5
    OFF_TEST = 6
    LOCKED = 7

    def __init__(self, mode):
        self._mode = mode

    def __repr__(self):
        mapping = {
            self.IDLE : 'IDLE',
            self.TEST : 'TEST',
            self.ALERT : 'ALERT',
            self.FIRE : 'FIRE',
            self.ATTACK : 'ATTACK',
            self.FIRE_ATTACK : 'FIRE_ATTACK',
            self.LOCKED : 'LOCKED',
            self.OFF_TEST : 'OFF_TEST'
        }
        return '<Mode "%s">' % mapping[self._mode]

    def __eq__(self, o):
        return isinstance(o, self.__class__) and self._mode == o._mode

    @classmethod
    def idle(cls):
        return Mode(cls.IDLE)

    @classmethod
    def test(cls):
        return Mode(cls.TEST)

    @classmethod
    def alert(cls):
        return Mode(cls.ALERT)

    @classmethod
    def fire(cls):
        return Mode(cls.FIRE)

    @classmethod
    def attack(cls):
        return Mode(cls.ATTACK)

    @classmethod
    def fire_attack(cls):
        return Mode(cls.FIRE_ATTACK)

    @classmethod
    def off_test(cls):
        return Mode(cls.OFF_TEST)

    @classmethod
    def locked(cls):
        return Mode(cls.LOCKED)


class Button:
    TEST = 0
    ALERT = 1
    FIRE = 2
    ATTACK = 3
    CANCEL = 4


class AFTimer:
    def __init__(self, siren_cls):
        self._mode = Mode.idle()

        self._led_alarm = LED(ALERT_LED_GPIO)
        self._led_ready = LED(READY_LED_GPIO)

        self._test_button = GPIOButton(TEST_BUTTON_GPIO)
        self._test_button.pin.bounce = 0.05
        self._test_button.when_pressed = functools.partial(self._button_pressed, Button.TEST)
        self._test_button.when_released = functools.partial(self._button_released, Button.TEST)

        self._alert_button = GPIOButton(ALERT_BUTTON_GPIO)
        self._alert_button.pin.bounce = 0.05
        self._alert_button.when_pressed = functools.partial(self._button_pressed, Button.ALERT)
        self._alert_button.when_released = functools.partial(self._button_released, Button.ALERT)

        self._fire_button = GPIOButton(FIRE_BUTTON_GPIO)
        self._fire_button.pin.bounce = 0.05
        self._fire_button.when_pressed = functools.partial(self._button_pressed, Button.FIRE)
        self._fire_button.when_released = functools.partial(self._button_released, Button.FIRE)

        self._attack_button = GPIOButton(ATTACK_BUTTON_GPIO)
        self._attack_button.pin.bounce = 0.05
        self._attack_button.when_pressed = functools.partial(self._button_pressed, Button.ATTACK)
        self._attack_button.when_released = functools.partial(self._button_released, Button.ATTACK)

        self._cancel_button = GPIOButton(CANCEL_BUTTON_GPIO)
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

        self._button_mapping = {
            Button.TEST : self._test_button,
            Button.ALERT : self._alert_button,
            Button.FIRE : self._fire_button,
            Button.ATTACK : self._attack_button,
            Button.CANCEL : self._cancel_button,
        }

        print('AF timer configured with siren %s' % self._siren)
        print('Panel ready.')

    def _get_buttons_pushed(self):
        """ Returns a set containing the button that are currently pressed. """
        buttons_pushed = set()
        buttons = []
        for button, obj in self._button_mapping.items():
            if obj.is_pressed:
                buttons_pushed.add(button)

        return buttons_pushed

    def _button_released(self, button):
        with self._button_push_lock:
            if self._mode == Mode.locked():
                return

            pressed = self._get_buttons_pushed()
            if button == Button.CANCEL and len(pressed) == 0:
                # The cancel button was just released, and now no buttons are pressed.
                self.change_mode(Mode.idle())
                return

            if self._mode == Mode.test() and button == Button.TEST:
                self.change_mode(Mode.idle())
            elif self._mode == Mode.test() or (
                    self._mode == Mode.off_test() and Button.CANCEL in pressed):
                if button == Button.ALERT:
                    self._siren._set_damper_low(False)
                elif button == Button.FIRE:
                    self._siren._set_damper_high(False)
            elif button == Button.CANCEL:
                self.change_mode(Mode.idle())

    def _button_pressed(self, button):
        """ Called whenever a button push event is called.

        This can be called from multiple threads, and so needs to be thread-safe.
        """
        # Take the lock so we ensure we're only processing one mode change at a time.
        with self._button_push_lock:
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
            if self._mode == Mode.locked():
                # The buttons don't work when locked.
                return

            pressed = self._get_buttons_pushed()
            if (self._mode == Mode.test() and Button.TEST in pressed) or (
                    self._mode == Mode.off_test() and Button.CANCEL in pressed):
                # Two additional buttons are allowed, and don't change modes, but do change what
                # the siren does.
                if button == Button.ALERT:
                    self._siren._set_damper_low(True)
                elif button == Button.FIRE:
                    self._siren._set_damper_high(True)

            elif self._mode == Mode.attack() and Button.ATTACK in pressed:
                if button == Button.FIRE:
                    self.change_mode(Mode.fire_attack())

            elif self._mode == Mode.fire() and Button.FIRE in pressed:
                if button == Button.ATTACK:
                    self.change_mode(Mode.fire_attack())

            elif self._mode == Mode.alert() and Button.ALERT in pressed:
                pass
            elif self._mode == Mode.fire_attack() and Button.FIRE in pressed and Button.ATTACK in pressed:
                pass
            else:
                # From here, we got a single button push, meaning there's a first-level mode switch.
                if button == Button.TEST:
                    self.change_mode(Mode.test())
                elif button == Button.ALERT:
                    self.change_mode(Mode.alert())
                elif button == Button.FIRE:
                    self.change_mode(Mode.fire())
                elif button == Button.ATTACK:
                    self.change_mode(Mode.attack())
                elif button == Button.CANCEL:
                    self.change_mode(Mode.off_test())

    def _run_in_thread(self, callable, duration=None):
        self.cancel()

        def wrapper():
            self._led_alarm.on()
            callable(duration)
            self._led_alarm.off()
            self._thread = None
            self.change_mode(Mode.idle())

        print("Run in thread: %s", callable.__repr__())
        self._thread = threading.Thread(target=wrapper)
        self._thread.start()

    def change_mode(self, mode: Mode, duration=None):
        """ Change to the specified mode, actuating the siren accordingly. """
        print(f"Change mode: {mode} from {self._mode} (duration: {duration})")
        if mode == Mode.idle():
            self.cancel()
        elif mode == Mode.off_test():
            self.cancel(Mode.off_test())
        elif mode == Mode.alert():
            self.alert(duration)
        elif mode == Mode.fire():
            self.fire(duration)
        elif mode == Mode.fire_attack():
            self.fire_attack(duration)
        elif mode == Mode.attack():
            self.attack(duration)
        elif mode == Mode.test():
            self.test()
        elif mode == Mode.locked():
            self.lock()
        else:
            print("Invalid mode: ", mode)
        print("Mode now ", self._mode)

    def test(self):
        self._run_in_thread(self._siren._on_test)
        self._mode = Mode.test()

    def alert(self, duration=None):
        self._run_in_thread(self._siren._on_alert, duration)
        self._mode = Mode.alert()

    def fire(self, duration=None):
        self._run_in_thread(self._siren._on_fire, duration)
        self._mode = Mode.fire()

    def attack(self, duration=None):
        self._run_in_thread(self._siren._on_attack, duration)
        self._mode = Mode.attack()

    def fire_attack(self, duration=None):
        self._run_in_thread(self._siren._on_fire_attack, duration)
        self._mode = Mode.fire_attack()

    def cancel(self, mode=None):
        with self._cancel_lock:
            print("Cancelling")
            self._cancel_cond.notify_all()

        if self._thread is not None:
            self._thread.join()
            print("cancelled")
            self._thread = None
        self._led_ready.on()
        self._mode = mode or Mode.idle()

    def lock(self):
        self.cancel()
        self._led_ready.blink(0.5, 0.5)
        self._mode = Mode.locked()

    def unlock(self):
        self.cancel(Mode.idle())

    def is_on(self):
        return self._mode != Mode.idle()

    def generate_api_mappings(self):
        mappings = {
            'tone': {
                'alert': functools.partial(self.change_mode, Mode.alert()),
                'fire': functools.partial(self.change_mode, Mode.fire()),
                'attack': functools.partial(self.change_mode, Mode.attack()),
                'fire_attack': functools.partial(self.change_mode, Mode.fire_attack()),
            },
            'control': {
                'lock': functools.partial(self.change_mode, Mode.locked()),
                'unlock': functools.partial(self.change_mode, Mode.idle()),
            },
            'debug': {
                'high': self._siren._set_damper_high,
                'low': self._siren._set_damper_low,
                'test': functools.partial(self.change_mode, Mode.test()),
            },
            'on': functools.partial(self.change_mode, Mode.alert()),
            'off': functools.partial(self.change_mode, Mode.idle()),
            'is_on': self.is_on,
        }
        return mappings

    def generate_console_mappings(self):
        mappings = {
            'high': self._siren._set_damper_high,
            'low': self._siren._set_damper_low,
            'test': functools.partial(self.change_mode, Mode.test()),
            'alert': functools.partial(self.change_mode, Mode.alert()),
            'fire': functools.partial(self.change_mode, Mode.fire()),
            'attack': functools.partial(self.change_mode, Mode.attack()),
            'fire_attack': functools.partial(self.change_mode, Mode.fire_attack()),
            'cancel': functools.partial(self.change_mode, Mode.idle()),
            'lock': functools.partial(self.change_mode, Mode.locked()),
            'unlock': functools.partial(self.change_mode, Mode.idle()),
        }
        return mappings
