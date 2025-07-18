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
import glob

class RotaryTable:
    def __init__(self, woodpecker):
        self.woodpecker = woodpecker

    def select_port_a_to_arm(self):
        self.woodpecker.grbl.gs.j("X.0 F2000")
        self.woodpecker.grbl.wait_idle()

    def select_port_b_to_arm(self):
        """
        X=4 => 5 degrees CW
        180 / 5 * 4 = 144
        """
        self.woodpecker.grbl.gs.j("X-144 F2000")
        self.woodpecker.grbl.wait_idle()

class Theta3:
    """
    Entire arc is around 2.2
    """
    def __init__(self, woodpecker):
        self.woodpecker = woodpecker
        self.off_home = -7
        self.off_center = -5.63
        """
        0.9 degree stepper
        360 / 0.9 => 400 steper per rev
        Not sure what GRBL internal scale factor is set to but this looks reasonable
        """
        self.degrees_per_unit = -90
        self.homed = False

    def home(self):
        """"
        (gently) crash r / phi3 to set its position
        1.37 from end
        """
        print("Theta3: homing")
        self.woodpecker.grbl.gs.j("Y-7 F60")
        self.wait_idle()
        time.sleep(0.2)
        # self.woodpecker.grbl.gs.j("Y-3.63 F100")
        self.woodpecker.grbl.gs.j("Y-5.63 F60")
        self.wait_idle()
        time.sleep(0.2)
        self.homed = True

    def home_lazy(self):
        if not self.homed:
            self.home()

    def move(self, r, block=True):
        """
        r from -180 to 180
        CCW angles are, by Evezor convention, positive, but negative y values are CCW 
        """
        value = r / self.degrees_per_unit  + self.off_center
        print("Theta3: setting %0.3f => %0.3f" % (r, value))
        self.woodpecker.grbl.gs.j("Y%0.3f F60" % value)
        if block:
            self.wait_idle()

    def wait_idle(self):
        self.woodpecker.grbl.wait_idle()

class LaserZ:
    def __init__(self, woodpecker):
        self.woodpecker = woodpecker

class Woodpecker:
    def __init__(self, verbose=False):
        ports = glob.glob("/dev/ttyUSB*")
        print("Woodpecker: found %u /dev/ttyUSB" % len(ports))
        if len(ports) == 1:
            print("Woodpecker: 1 ports, assuming USB0")
            port = "/dev/ttyUSB0"
        elif len(ports) == 2:
            print("Woodpecker: 2 ports, assuming USB1")
            port = "/dev/ttyUSB1"
        else:
            assert 0, "Failed to find"

        self.grbl = GRBL(verbose=verbose, port=port)
        self.rt = RotaryTable(self)
        self.theta3 = Theta3(self)
        self.laserz = LaserZ(self)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Woodpecker GRBL controller for rotary table, theta3, and laser Z")
    add_bool_arg(parser, "--verbose", default=False, help="Verbose output")
    parser.add_argument("--theta3", type=float, default=None)
    add_bool_arg(parser, "--home", default=True, help="Home at startup")
    args = parser.parse_args()

    w = Woodpecker()

    if 0:
        print("Selecting port A")
        w.rt.select_port_a_to_arm()
        print("Selecting port B")
        w.rt.select_port_b_to_arm()
        print("Selecting port A")
        w.rt.select_port_a_to_arm()

    if 0:
        w.theta3.home()
        w.theta3.move(0)
        w.theta3.move(90)
        w.theta3.move(-90)

    if args.home:
        print("Homing")
        w.theta3.home()

    if args.theta3 is not None:
        print("Moving", args.theta3)
        w.theta3.move(args.theta3)

if __name__ == "__main__":
    main()
