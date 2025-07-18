#!/usr/bin/env python3
"""
https://www.amazon.com/dp/B098T5KGTS?ref=ppx_yo2ov_dt_b_fed_asin_title
Waveshare Industrial 8-Channel Relay Module for Raspberry Pi Pico Power Supply Isolation Photocoupler Isolation

"""
import belay
import time

device = belay.Device("/dev/ttyACM0")

device("""
from machine import Pin

ch1 = Pin(21, mode=Pin.OUT, value=0)
ch2 = Pin(20, mode=Pin.OUT, value=0)
ch3 = Pin(19, mode=Pin.OUT, value=0)
ch4 = Pin(18, mode=Pin.OUT, value=0)
ch5 = Pin(17, mode=Pin.OUT, value=0)
ch6 = Pin(16, mode=Pin.OUT, value=0)
ch7 = Pin(15, mode=Pin.OUT, value=0)
ch8 = Pin(14, mode=Pin.OUT, value=0)
""")

@device.task
def set_blue(state):
    ch1.value(state)

@device.task
def set_green(state):
    ch2.value(state)

@device.task
def set_orange(state):
    ch3.value(state)

@device.task
def set_red(state):
    ch4.value(state)

@device.task
def set_beeper(state):
    ch5.value(state)

def main():
    try:
        while True:
            set_blue(1)
            time.sleep(0.5)
            set_blue(0)

            time.sleep(0.5)

            set_green(1)
            time.sleep(0.5)
            set_green(0)

            time.sleep(0.5)

            set_orange(1)
            time.sleep(0.5)
            set_orange(0)

            time.sleep(0.5)

            set_red(1)
            time.sleep(0.5)
            set_red(0)

            time.sleep(0.5)
    finally:
        set_blue(0)
        set_red(0)
        set_orange(0)
        set_green(0)

if __name__ == "__main__":
    main()
