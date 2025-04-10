""" Fake class implementing the gpiozero functions used. """
print("Using fake gpiozero")

class Pin:
    def __init__(self):
        self.bounce = None


class LED:
    def __init__(self, gpio):
        self.gpio = gpio
        self.pin = Pin()
        self._on = False
        
    def __repr__(self):
        return '<LED %d: %s>' % (
            self.gpio,
            self._on and 'on' or 'off'
        )

    def on(self):
        self._on = True

    def off(self):
        self._on = False


class Button:
    def __init__(self, gpio):
        self.gpio = gpio
        self.pin = Pin()

        self.when_pressed = None
        self.when_released = None

    def press(self):
        self.hold()
        self.release()

    def hold(self):
        if self.when_pressed is not None:
            self.when_pressed()

    def release(self):
        if self.when_released is not None:
            self.when_released()
