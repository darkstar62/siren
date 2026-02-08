#!/usr/bin/python3

""" Main program for the siren and AF timer runtime. """

from console import Console
from model.fs3t22a import FS3T22A
from rest import run_rest
from timer.af_timer import AFTimer, Mode, Button

import functools
from threading import Thread


HOST = '0.0.0.0'
PORT = 12345


def run_console(port, af_timer: AFTimer):
    locals = af_timer.generate_console_mappings()
    locals.update({
        'Mode': Mode,
        'Button': Button,
    })
    
    def thread(port, locals):
        while True:
            print("Starting new console")
            console = Console(HOST, port)
            console.run_server(locals)

    console_thread = Thread(target=thread, kwargs={'port': port, 'locals': locals})
    console_thread.start()
    return console_thread

if __name__ == "__main__":
    import argparse
    import functools
    parser = argparse.ArgumentParser(description="AF Timer main runtime.")
    parser.add_argument("--console_port", type=int, default=PORT, help="Port to run the console telnet service on")
    args = parser.parse_args()

    af_timer = AFTimer(FS3T22A)
    console_thread = run_console(args.console_port, af_timer)

    run_rest(af_timer)
    console_thread.join()
