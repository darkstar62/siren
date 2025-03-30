""" Solenoid functionality. """

import threading
import time

class Solenoid:
    MAX_ON_TIME = 5

    def __init__(self, relay):
        self._relay = relay
        self._relay.off()

        self._thread = None
        self._cancel_lock = threading.Lock()
        self._cancel_cond = threading.Condition(self._cancel_lock)

    def on(self):
        """ Turn the solenoid on, optionally for `how_long` seconds.

        If not specified, the max runtime is used to protect the
        solenoid.
        """
        self._relay.on()

        def watchdog():
            for t in range(self.MAX_ON_TIME):
                with self._cancel_lock:
                    if self._cancel_cond.wait(1):
                        break
            self._relay.off()
            self._thread = None

        if self._thread is None:
            self._thread = threading.Thread(target=watchdog)
            self._thread.start()

    def off(self):
        """ Turn the siren motor off. """
        self._relay.off()
        with self._cancel_lock:
            self._cancel_cond.notify_all()

        if self._thread is not None:
            self._thread.join()
            self._thread = None

