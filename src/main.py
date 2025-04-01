#!/usr/bin/python3

""" Main program for the siren and AF timer runtime. """

from console import Console
import functools

HOST = '0.0.0.0'
PORT = 12345

if __name__ == "__main__":
    from model.fs3t22a import FS3T22A
    from timer.af_timer import AFTimer, Mode, Button
    import argparse
    import time

    parser = argparse.ArgumentParser(description="AF Timer main runtime.")
    parser.add_argument("--console_port", type=int, default=PORT, help="Port to run the console telnet service on")
    args = parser.parse_args()

    af_timer = AFTimer(FS3T22A)
    console = Console(HOST, args.console_port)
    locals = {
        'timer': af_timer,
        'siren': af_timer._siren,
        'high': af_timer._siren._set_damper_high,
        'low': af_timer._siren._set_damper_low,
        'test': af_timer.test,
        'alert': af_timer.alert,
        'fire': af_timer.fire,
        'attack': af_timer.attack,
        'fire_attack': af_timer.fire_attack,
        'cancel': af_timer.cancel,
        'Mode': Mode,
        'Button': Button,
    }
    while True:
        console.run_server(locals=locals)