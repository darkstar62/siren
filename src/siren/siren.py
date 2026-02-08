""" Interface for any siren driven by the A11 AF Timer. """

import threading
from . import LED_ALARM


class Siren:
    """
    Interface for implementing a siren to be driven by the AF 11 timer.

    The AF timer implemented by this software has five buttons: Test,
    Alert, Fire, Attack, and Cancel.  Depending on the siren attached,
    some of these buttons may or may not have a function,  For example,
    if the timer is attached to a 2T22 siren, the "Fire" alert wouldn't
    have a function, as there are no solenoids on that siren.

    Each siren implementation is expected to derive from this class and
    implement whatever functionality makes sense.  The mode of operation
    of the siren can be customized as well.

    Note that each event function is called in a thread that can be
    cancelled.  To detect cancellation, use the `_wait_for_cancel` function.
    """

    def __init__(self, cancel_lock, cancel_cond):
        self._cancel_cond = cancel_cond
        self._cancel_lock = cancel_lock

    def _on_test(self, duration=None):
        """ Called when the "Test" button is pressed. """

    def _on_alert(self, duration=None):
        """ Called when the "Alert" button is pressed. """

    def _on_fire(self, duration=None):
        """ Called when the "Fire" button is pressed. """

    def _on_fire_attack(self, duration=None):
        """ Called when the "Fire" and "Attack" buttons are pressed. """

    def _on_attack(self, duration=None):
        """ Called when the "Attack" button is pressed. """

    def _set_damper_high(self, closed):
        """ Close the high damper if `closed` is set. """

    def _set_damper_low(self, closed):
        """ Close the low damper if `closed` is set. """

    def _wait_for_cancel(self, timeout=None):
        """ A utility function that implementations can use to interruptably sleep.

        Args:
          timeout: Optional time in seconds to delay.

        Returns:
          True if the "Cancel" button was pushed (or "Test" was released) before the timeout,
          False if the timeout expired.
        """
        with self._cancel_lock:
            return self._cancel_cond.wait(timeout)

