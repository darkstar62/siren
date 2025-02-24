""" Interface for any siren driven by the A11 AF Timer. """

import threading
from . import LED_ALARM


class Siren:
    def __init__(self, cancel_lock, cancel_cond):
        self._cancel_cond = cancel_cond
        self._cancel_lock = cancel_lock

    def _on_test(self):
        pass

    def _on_alert(self):
        pass

    def _on_fire(self):
        pass

    def _on_attack(self):
        pass

    def _wait_for_cancel(self, timeout=None):
        with self._cancel_lock:
            return self._cancel_cond.wait(timeout)

