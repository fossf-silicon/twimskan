#!/usr/bin/env python3
import belay

device = belay.Device("/dev/ttyACM0")

device("""
#from machine import Pin
""")

@device.task
def move(state):
    print("fixme")

