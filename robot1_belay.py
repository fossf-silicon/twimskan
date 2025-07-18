#!/usr/bin/env python3
"""
https://belay.readthedocs.io/en/latest/api.html
https://github.com/fossf-silicon/twimskan/blob/main/esp32-main-copied/GRBLScara.py

screen /dev/ttyUSB0 115200

import belay
device = belay.Device("/dev/ttyUSB0")

"""
import belay
import time

# Belay likes to reset environment
# Disable it so we keep machine state
if 1:
    print("Disabling soft reset")
    from belay.pyboard import Pyboard

    orig_enter_raw_repl = Pyboard.enter_raw_repl
    def wrap_enter_raw_repl(self, soft_reset=True):
        orig_enter_raw_repl(self, soft_reset=False)
    Pyboard.enter_raw_repl = wrap_enter_raw_repl

print("Connecting...")
device = belay.Device("/dev/ttyUSB0")

def initialize():
    if 0:
        # about 18 seconds
        device.soft_reset()
        time.sleep(20)

    print("Query")

    device("""
#from machine import Pin
# <class 'GRBLScara'>
grbl = iris.locals['grbl']
#gene = iris.locals['gene']

def sync_gen():
    while grbl.gen.gen:
        grbl.gen.next(None)
""")
initialize()

# hack to make vscode happy
grbl=None

@device.task


@device.task
def robot_init():
    grbl.home('p')
    sync_gen()

    grbl.home('h')
    sync_gen()

    grbl.home('z')
    sync_gen()

@device.task
def grbl_move_t(t):
    grbl.move(t=t)

@device.task
def grbl_move_z(z):
    grbl.move(z=z)

@device.task
def grbl_gui():
    return grbl.gui()

@device.task
def grbl_disable_motors():
    """
    WARNING: this will not complete untl a feed finishes
    """
    grbl.disable_motors()

@device.task
def grbl_enable_motors():
    grbl.enable_motors()

@device.task
def grbl_feed_hold():
    grbl.feed_hold()

def estop():
    # best we can do right now
    grbl_feed_hold()

@device.task
def grbl_get_pos_cartesian():
    """
    >>> grbl.get_pos()
    {'y': -165.198, 'x': 196.949, 'z': 0.0}
    """
    return grbl.get_pos()

@device.task
def grbl_get_pos_scara():
    """
    >>> grbl.get_pos(kinematics="scara")
    {'t_encoder': 0.02197266, 'p': 100.021, 't': 0.0, 'p_encoder': 100.0635, 'z': 0.0}
    """
    return grbl.get_pos(kinematics="scara")

def soft_reset(sleep=True):
    # about 18 seconds
    device.soft_reset()
    if sleep:
        time.sleep(20)

def control_c():
    device._board.serial.write(b"\x03")
    device._board.serial.flush()
