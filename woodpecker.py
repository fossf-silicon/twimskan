#!/usr/bin/env python3

"""
X
    rotary table
    X=4 => 5 degrees CW
    need to rate CCW or will crash...
"""

from uscope.motion.grbl import GRBL
from uscope.util import add_bool_arg
import time

class RotaryTable:
    def __init__(self, woodpecker):
        self.woodpecker = woodpecker

    def select_port_a(self):
        self.woodpecker.grbl.gs.j("X.0 F2000")
        self.woodpecker.grbl.wait_idle()

    def select_port_b(self):
        """
        X=4 => 5 degrees CW
        180 / 5 * 4 = 144
        """
        self.woodpecker.grbl.gs.j("X-144 F2000")
        self.woodpecker.grbl.wait_idle()

class Theta3:
    def __init__(self, woodpecker):
        self.woodpecker = woodpecker

class LaserZ:
    def __init__(self, woodpecker):
        self.woodpecker = woodpecker

class Woodpecker:
    def __init__(self, verbose=False):
        self.grbl = GRBL(verbose=verbose)
        self.rt = RotaryTable(self)
        self.theta3 = Theta3(self)
        self.laserz = LaserZ(self)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Woodpecker GRBL controller for rotary table, theta3, and laser Z")
    add_bool_arg(parser, "--verbose", default=False, help="Verbose output")

    w = Woodpecker()

    if 0:
        print("Selecting port A")
        w.rt.select_port_a()
        print("Selecting port B")
        w.rt.select_port_b()
        print("Selecting port A")
        w.rt.select_port_a()


if __name__ == "__main__":
    main()
