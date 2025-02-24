""" Solenoid functionality. """

class Solenoid:
    def __init__(self, relay):
        self._relay = relay
        self._relay.off()

    def on(self):
        """ Turn the solenoid on, optionally for `how_long` seconds.

        If not specified, the max runtime is used to protect the
        solenoid.
        """
        self._relay.on()

    def off(self):
        """ Turn the siren motor off. """
        self._relay.off()