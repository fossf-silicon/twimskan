#!/usr/bin/env python3
"""
WARNING: StdIn on micropython side was modified to make parsing easier
<return>reply</return>
"""
import time
import sys

import serial
from pexpect_serial import SerialSpawn
import ast
from collections import OrderedDict

class GrblTimeout(Exception):
    pass

class RobotArm:
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.01)
        self.ss = SerialSpawn(self.serial)

    def robot_init(self):
        self.home_p(block=True)
        self.home_t(block=True)
        self.home_z(block=True)

    def command(self, s):
        verbose = False
        verbose and print("Sending")
        self.ss.sendline(s)
        verbose and print("Checking")
        self.ss.expect('</return>', timeout=1)
        before = self.ss.before.decode("ascii")
        if verbose:
            print("")
            print("")
            print("")
            print("before '%s'" % before)
            print("")
            print("")
            print("")
        p1 = before.find("<return>")
        assert p1 >= 0
        ret = before[p1 + len("<return>"):]
        verbose and print("ret", ret)
        # print(ret)
        # XXX: can't use safe functions because of OrderedDict
        ret = eval(ret)
        verbose and print("ok")
        return ret

    def nop(self):
        assert self.command("{}") == {}

    def home_p(self, block=True, closed_loop=False):
        self.command("grbl.home('p')")
        if block:
            if closed_loop:
                # HACK: command can go in before we check status :(
                time.sleep(1.0)
                self.wait_idle(timeout=3)
            else:
                # FIXME: measure
                time.sleep(0.5)

    def home_t(self, block=True, closed_loop=False):
        self.command("grbl.home('t')")
        if block:
            if closed_loop:
                # HACK: command can go in before we check status :(
                time.sleep(1.0)
                self.wait_idle(timeout=3)
            else:
                # FIXME: measure
                time.sleep(0.5)

    def home_z(self, block=True):
        self.command("grbl.home('z')")
        if block:
            # HACK: command can go in before we check status :(
            # 0.6 sec is not enough, 0.7 min
            time.sleep(1.0)
            self.wait_idle(timeout=30)

    def grbl_disable_motors(self):
        """
        WARNING: this will not complete untl a feed finishes
        """
        assert self.command("grbl.disable_motors()") == None

    def grbl_enable_motors(self):
        assert self.command("grbl.enable_motors()") == None

    def gui(self):
        """
        {'type': 'GRBLScara', 'theta_len': 200, 'work_offsets': OrderedDict({'machine': {'y': 0, 'x': 0, 'z': 0}, 'board_offset': {'y': 0, 'x': 0, 'z': 0}}), 'tool_offset': 'default', 'name': 'grbl', 'tool_offsets': OrderedDict({'default': {'z': 0, 'p': 0, 'l': 200}, 'camera': {'z': 10, 'p': -20, 'l': 210}}), 'work_offset': 'machine', 'axes_map': OrderedDict({'x': 't', 'y': 'p', 'z': 'z'}), 'pid': 11895, 'axes': ['x', 'y', 'z']}
        """
        return self.command("grbl.gui()")

    def wait_idle(self, timeout=1.0):
        tstart = time.time()
        while True:
            status = self.status()
            print("status", status)
            if status["state"] == "Idle":
                return
            dt = time.time() - tstart
            if dt >= timeout:
                raise GrblTimeout()


    def status(self):
        # {'state': 'Idle', 'limits': '', 'MPos': {'y': 71.519, 'x': 0.0, 'z': 250.0}}
        return self.command("grbl.status")

    def grbl_get_pos_cartesian(self):
        """
        >>> grbl.get_pos()
        {'y': -165.198, 'x': 196.949, 'z': 0.0}
        """
        return self.command("grbl.get_pos()")

    def grbl_get_pos_scara(self):
        """
        >>> grbl.get_pos(kinematics="scara")
        {'t_encoder': 0.02197266, 'p': 100.021, 't': 0.0, 'p_encoder': 100.0635, 'z': 0.0}
        """
        return self.command("grbl.get_pos(kinematics='scara')")

    def grbl_move_p(self, p, f=None, block=True, timeout=30):
        # FIXME: limits
        assert -180 <= p <= +180
        if f:
            self.command(f"grbl.move(p={p})")
        else:
            self.command(f"grbl.move(p={p}, f={f})")
        if block:
            time.sleep(1.0)
            self.wait_idle(timeout=timeout)

    def grbl_move_t(self, t, f=None, block=True, timeout=30):
        # FIXME: limits
        assert -180 <= t <= +180
        if f:
            self.command(f"grbl.move(t={t})")
        else:
            self.command(f"grbl.move(t={t}, f={f})")
        if block:
            time.sleep(1.0)
            self.wait_idle(timeout=timeout)

    def grbl_move_z(self, z, f=None, block=True, timeout=30):
        assert 0 <= z <= 250
        if f:
            self.command(f"grbl.move(z={z})")
        else:
            self.command(f"grbl.move(z={z}, f={f})")
        if block:
            time.sleep(1.0)
            self.wait_idle(timeout=timeout)

    def grbl_feed_hold(self):
        self.command("grbl.feed_hold()")

    def estop(self):
        # best we can do right now
        self.grbl_feed_hold()

ra = RobotArm()
print("Send command")
# print("Got", ra.command("{}"))
print("Check nop")
ra.nop()
print("Check misc")
#print("Got", ra.command("grbl.home('z')"))
#print("Got", ra.grbl_disable_motors())
#print("Got", ra.grbl_enable_motors())
#print("Got", ra.gui())

print("status", ra.status())
print("pos cart", ra.grbl_get_pos_cartesian())
print("pos scara", ra.grbl_get_pos_scara())

if 0:
    ra.home_z(block=False)
    while True:
        print(ra.status())
        time.sleep(0.2)

if 0:
    print("Homing z")
    ra.home_z(block=True)

if 1:
    print("pos scara", ra.grbl_get_pos_scara())
    while True:
        ra.grbl_move_z(220, f=500)
        print("pos scara", ra.grbl_get_pos_scara())
        ra.grbl_move_z(240, f=500)
        print("pos scara", ra.grbl_get_pos_scara())


print("Done")
