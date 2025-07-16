#!/usr/bin/env python3

import belay
import time

# Otherwise we lose machine state
if 1:
    print("Disabling soft reset")
    from belay.pyboard import Pyboard

    orig_enter_raw_repl = Pyboard.enter_raw_repl
    def wrap_enter_raw_repl(self, soft_reset=True):
        orig_enter_raw_repl(self, soft_reset=False)
    Pyboard.enter_raw_repl = wrap_enter_raw_repl

print("Connecting...")
device = belay.Device("/dev/ttyUSB0")

if 0:
    # about 18 seconds
    device.soft_reset()
    time.sleep(20)

if 1:
    print("Interrupting...")
    device._board.serial.write(b"\x03")
    device._board.serial.flush()

    print("Sleeping")
    time.sleep(0.1)

print("Query")

device("""
#from machine import Pin
# <class 'GRBLScara'>
grbl = iris.locals['grbl']
""")
# hack to make vscode happy
#grbl=None

@device.task
def grbl_gui():
    '''
    some object in here can't return as is
    ValueError: malformed node or string on line 1: <ast.Call object at 0x7963428cbb90>
    {'type': 'GRBLScara', 'theta_len': 200, 'work_offsets': OrderedDict({'machine': {'y': 0, 'x': 0, 'z': 0}, 'board_offset': {'y': 0, 'x': 0, 'z': 0}}), 'tool_offset': 'default', 'name': 'grbl', 'tool_offsets': OrderedDict({'default': {'z': 0, 'p': 0, 'l': 200}, 'camera': {'z': 10, 'p': -20, 'l': 210}}), 'work_offset': 'machine', 'axes_map': OrderedDict({'x': 't', 'y': 'p', 'z': 'z'}), 'pid': 11895, 'axes': ['x', 'y', 'z']}
    '''
    return str(grbl.gui())

print(grbl_gui())

