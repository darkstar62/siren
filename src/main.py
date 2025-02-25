#!/usr/bin/python3

""" Main program for the siren and AF timer runtime. """

if __name__ == "__main__":
    from model.fs3t22a import FS3T22A
    from timer.af_timer import AFTimer
    import time

    af_timer = AFTimer(FS3T22A)

    while True:
        time.sleep(1)
