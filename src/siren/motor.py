""" Motor control for the AF timer. """

class Motor:
    def __init__(self, relay):
        self._relay = relay
        self._relay.off()

    def on(self):
        """ Turn the siren motor on. """
        self._relay.on()

    def off(self):
        """ Turn the siren motor off. """
        self._relay.off()