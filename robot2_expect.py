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
import datetime

def printt(format, *args, **kwargs):
    print(str(datetime.datetime.now().isoformat()) + ": " + format, *args, **kwargs)

class GrblTimeout(Exception):
    pass

def format_scara_pos(pos):
    if len(pos) == 0:
        return ""
    elif len(pos) == 1:
        return "%c=%0.3f" % (list(pos.keys())[0], list(pos.values())[0])
    elif len(pos) == 2:
        assert 'p' in pos and 't' in pos
        return "t=%0.3f p=%0.3f" % (pos['t'],pos['p'])
    elif len(pos) == 3:
        assert 'p' in pos and 't' in pos and 'z' in pos
        return "t=%0.3f p=%0.3f z=%0.3f" % (pos['t'], pos['p'], pos['z'])
    else:
        assert 0, pos

def assert_max_axis_error(pos_want, pos_got, tolerance=1):
    for k in pos_want.keys():
        delta = abs(pos_got[k] - pos_want[k])
        assert delta < tolerance, (pos_want, pos_got)

def within_max_axis_error(pos_want, pos_got, tolerance=1):
    for k in pos_want.keys():
        delta = pos_got[k] - pos_want[k]
        printt("within_max_axis_error: check %s: want %s, got %s, want delta %s < tolerance %s" % (k, pos_want[k], pos_got[k], delta, tolerance))
        delta = abs(delta)
        if delta > tolerance:
            printt("  within_max_axis_error: axis fail")
            return False
        printt("  within_max_axis_error: axis ok")
        printt("  within_max_axis_error: ok")
    return True

def pos2tpz(pos):
    ret = {}

    for k in "tpz":
        v = pos.get(k)
        if v is None:
            continue
        ret[k] = v
    return ret

def encoder2pos(pos, z=False):
    """
    Take position w/ supplamental encoder info and convert it to a normal t / p
    z is not included by default
    """
    ret = {}

    for k in "tp":
        v = pos.get(k + "_encoder")
        if v is None:
            continue
        ret[k] = v
    if z:
        v = pos.get("z")
        if v is not None:
            ret["z"] = v
    return ret

def encoded_pos(pos):
    """
    Only axes that have encoders (t, p)
    """
    ret = {}

    for k in "tp":
        v = pos.get(k)
        if v is None:
            continue
        ret[k] = v
    return ret

class PositionTimeout(Exception):
    pass

def check_position(ra, pos_want, pos_final, settle_timeout=0.6):
    tstart = time.time()
    print("check_position: GRBL")
    while True:
        # This should be really tight (within 0.001)
        # If GRBL didn't obey us something fundamental is wrong
        # I've seen 0.003, shrug
        # p=112.039 vs p=112.036
        if within_max_axis_error(pos_want, pos_final, tolerance=0.005):
            break
        if time.time() - tstart > settle_timeout:
            #assert_max_axis_error(pos_want, pos_final, tolerance=0.002)
            raise PositionTimeout("Failed to settle (GRBL) %s %s" % (pos_want, pos_final))
        pos_final = ra.grbl_get_pos_scara()
        time.sleep(0.05)
        print("Not within tolerance (GRBL), checking again")

    # encoders are slow to update
    # Noise around 0.04 degree
    # Look for gross errors to start
    print("check_position: encoder")
    pos_final = encoder2pos(pos_final)
    pos_want = encoded_pos(pos_want)
    while True:
        if 0:
            deltas = {}
            for k, v in pos_want.items():
                deltas[k] = pos_final[k + "_encoder"] - pos_want[k]
            print("  Encoder error: " + format_scara_pos(deltas))
        # FIXME: lower for now to see if we can make progress reliably
        # if within_max_axis_error(pos_want, pos_final, tolerance=0.1):
        if within_max_axis_error(pos_want, pos_final, tolerance=0.6):
            break
        if time.time() - tstart > settle_timeout:
            #assert_max_axis_error(pos_want, pos_final, tolerance=0.1)
            raise PositionTimeout("Failed to settle (encoder) %s %s" % (pos_want, pos_final))
        pos_final = encoder2pos(ra.grbl_get_pos_scara())
        time.sleep(0.05)
        print("Not within tolerance (encoder), checking again")

    print("check_position: ok")

class GrblWrap:
    def __init__(self, ra):
        self.ra = ra

    def move(self, block=True, timeout=30.0, check=True, **kwargs):
        settle_timeout = 3.0
        moves = ", ".join(["%s=%s" % (k, v) for k, v in sorted(kwargs.items())])
        self.ra.command(f"grbl.move({moves})")
        if block:
            tstart = time.time()
            # 0.6 not enough
            # be really conservative for now
            print("Sent move. Waiting for idle")
            time.sleep(1.2)
            self.ra.wait_idle(timeout=timeout)
            if check:
                print("Verifying position was reached")
                pos_want = dict(kwargs)
                pos_want = encoded_pos(pos_want)
                pos_final = self.ra.grbl_get_pos_scara()
                # should already be here if its going to happen
                # XXX: in practice I need to add more wait here
                check_position(self.ra, pos_want, pos_final, settle_timeout=1.2)
  
        else:
            assert 0, "everything should block right now"



class RobotArm:
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.01)
        self.ss = SerialSpawn(self.serial)
        self.grbl = GrblWrap(self)
        self.station = None

    def robot_init(self):
        self.home_t(block=True)
        self.home_p(block=True)
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

    # maybe instead of open loop
    # have a quick version for when difference should be small

    def home_p(self, block=True, closed_loop=True):
        self.command("grbl.home('p')")
        if block:
            if closed_loop:
                # HACK: command can go in before we check status :(
                time.sleep(1.0)
                self.wait_idle(timeout=20)
            else:
                assert 0, "doesn't work"
                # FIXME: measure
                time.sleep(0.5)

    def home_t(self, block=True, closed_loop=True):
        self.command("grbl.home('t')")
        if block:
            if closed_loop:
                # HACK: command can go in before we check status :(
                time.sleep(1.0)
                self.wait_idle(timeout=20)
            else:
                assert 0, "doesn't work"
                # FIXME: measure
                time.sleep(0.5)

    def home_z(self, block=True):
        self.command("grbl.home('z')")
        if block:
            # HACK: command can go in before we check status :(
            # 0.6 sec is not enough, 0.7 min
            time.sleep(1.2)
            # takes a while if far down
            self.wait_idle(timeout=60)

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
        iter = 0
        while True:
            status = self.status()
            # print("status", status)
            if status["state"] == "Idle":
                #print("wait_idle: took %u iter" % iter)
                return
            dt = time.time() - tstart
            if dt >= timeout:
                raise GrblTimeout()
            time.sleep(0.05)
            iter += 1


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

    def move_pos(self, pos, f=None, block=True, timeout=30):
        print("move", pos)
        for k in pos.keys():
            assert k in 'ptz'
        moves = ", ".join(["%s=%s" % (k, v) for k, v in sorted(pos.items())])
        command = f"grbl.move({moves})"
        if f:
            command += f", f={f})"
        print("Command: " + command)
        self.command(command)
        if block:
            time.sleep(1.0)
            self.wait_idle(timeout=timeout)

    def grbl_feed_hold(self):
        self.command("grbl.feed_hold()")

    def estop(self):
        # best we can do right now
        self.grbl_feed_hold()

    def grbl_gene_next(self):
        """
        grbl.gene.next(None)
        This can fix a wedge
        However, once this happens generally the state is corrupted / no longer self clearing
        """
        self.command("grbl.gene.next(None)")

    def check_gene_corrupt(self):
        # FIXME: when this happens reboot arm and clear if possible
        pass

    def set_station(self, station):
        self.station = station

    def t_reset(self, value):
        """
        Active low
        """
        value = bool(value)
        self.command("x_reset(%s)" % (value,))

    def p_reset(self, value):
        """
        Active low
        """
        value = bool(value)
        self.command("y_reset(%s)" % (value,))

class RobotCell:
    def __init__(self):
        self.ra = RobotArm()
        # TODO: add grbl controller
        # TODO: add laser
        # TODO: add rp2040 for stack lights and such

def main():
    ra = RobotArm()
    grbl = ra.grbl
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

    print("Verifying idle")
    ra.wait_idle(timeout=1)

    print("pos cart", ra.grbl_get_pos_cartesian())
    pos_scara = ra.grbl_get_pos_scara()
    print("pos scara", pos_scara)
    # t / p are a bit safe to do automatically 
    if pos_scara['z'] == 0.0:
        # assert 0, "z not homed (probably). Home before continuing"
        print("Need to home Z")
        print("Ensure is clear")
        input("Press Enter to continue...")
        print("Homing z...")
        ra.home_z(block=True)
        print("Rough homing t...")
        ra.home_t(block=True)
        print("Rough homing p...")
        ra.home_p(block=True)
        print("Power up homing complete")

    try:

        if 0:
            ra.home_z(block=False)
            while True:
                print(ra.status())
                time.sleep(0.2)

        if 0:
            print("Homing z")
            ra.home_z(block=True)

        if 0:
            print("pos scara", ra.grbl_get_pos_scara())
            while True:
                ra.grbl_move_z(220, f=500)
                print("pos scara", ra.grbl_get_pos_scara())
                ra.grbl_move_z(240, f=500)
                print("pos scara", ra.grbl_get_pos_scara())

        print("starting moves")
        #ra.move_pos({'z':250.000}, f=100)
        if 0:
            ra.move_pos({'t':-31.750, 'p':-109.292}, f=100)
            ra.move_pos({'t':-86.506, 'p':67.698}, f=100)
            ra.move_pos({'t':10.854, 'p':133.308}, f=100)

        if 0:
            print("pos", ra.grbl_get_pos_scara())
            # where we should be / nop
            ra.move_pos({'t':-2.943, 'p':-90.989}, f=100)
            print("pos", ra.grbl_get_pos_scara())
            #ra.move_pos({'t':-29.399, 'p':-112.742}, f=100)

        if 0:
            print("pos", ra.grbl_get_pos_scara())
            print("homing")
            ra.home_p(block=True)
            ra.home_t(block=True)
            print("pos", ra.grbl_get_pos_scara())
            print("")
            print("")
            print("")
            # where we should be / nop
            ra.move_pos({'t': -34.651, 'p': -105.644}, f=100)
            print("")
            print("")
            print("")
            print("pos2", ra.grbl_get_pos_scara())
            print("")
            print("")
            print("")
            ra.move_pos({'t': -34.827, 'p': -48.867}, f=100)
            print("")
            print("")
            print("")
            print("pos3", ra.grbl_get_pos_scara())
            print("")
            print("")
            print("")
            ra.move_pos({'t': -80.684, 'p': 140.999}, f=100)

            if 0:
                ra.move_pos({'t': -25.422, 'p': 132.253}, f=100)
                print("")
                print("")
                print("")
                print("pos4", ra.grbl_get_pos_scara())
                print("")
                print("")
                print("")
                ra.move_pos({'t': 24.434, 'p': 134.055}, f=100)
                print("")
                print("")
                print("")
                print("pos5", ra.grbl_get_pos_scara())

        def safely_get_to_loadlock(homing=False):
            """
            """

            # 5000 lost a lot of steps
            print("")
            print("")
            print("")
            if homing:
                print("Rough position sync")
                ra.home_p(block=True)
                ra.home_t(block=True)
            print("Checking initial arm position to move to loadlock")
            start = ra.grbl_get_pos_scara()
            # are we by the wafer stations?
            if start['t'] > 0:
                # phi folded over sharpy for tight space over there
                assert start['p'] > 0
                print("Starting by user load/unload port")
                # Reverse earlier moves
                grbl.move(z=100, f=1000, check=not homing)
                grbl.move(t=24.434, p=122.498, f=2000, check=not homing)
                grbl.move(t=24.434, p=134.055, f=2000, check=not homing)
                grbl.move(t=-76.992, p=139.768, f=2000, check=not homing)
                grbl.move(t=-86.638, p=80.420, f=2000, check=not homing)
                grbl.move(t=-84.661, p=54.207, f=2000, check=not homing)
                grbl.move(t=-34.827, p=-48.867, f=2000, check=not homing)
            else:
                print("Starting closer to TwimSkan load lock")
                # corner is generally a safe move
                grbl.move(z=100, f=1000)
                grbl.move(t=-34.827, p=-48.867, f=2000, check=not homing)
                print("first move complete")
            # finally to station idle positon
            if homing:
                """
                High level notes:
                -Home once to get roughly in position, then another once we are closer to there => more reliable
                -Resetting stepper pulse count makes positioning more reliable
                -Encoders and steps are not aligned. But try to always do the same position for best consistency
                -Many sensors take a while to flush through the system
                """
                print("move to homing position")

                def move_homing1(check):
                    grbl.move(t=-20, p=-120, f=2000, check=check)
                    print("Restart homing1")
                    # Reset step count on driver
                    ra.t_reset(0)
                    ra.p_reset(0)
                    time.sleep(0.1)
                    ra.t_reset(1)
                    ra.p_reset(1)
                # Encoders take a while to settle
                # (0.5 to report position + 0.5 to transport)
                print("Starting fine position sync")
                move_homing1(check=False)
                time.sleep(1.2)
                print("Rough home p")
                ra.home_p(block=True)
                print("Rough home t")
                ra.home_t(block=True)
                if 1:
                    move_homing1(check=False)
                    # Encoders take a while to settle
                    # (0.5 to report position + 0.5 to transport)
                    time.sleep(1.2)
                    print("Fine home p")
                    ra.home_p(block=True)
                    print("Fine home t")
                    ra.home_t(block=True)
            print("Move to final position")
            grbl.move(t=-21.138, p=-128.760, f=2000)
            print("")
            print("")
            print("")

        def move_torture_test(f=2000):
            print("")
            print("")
            print("")
            print(f"Motion torture, f={f}")
            safely_get_to_loadlock()
            print("")
            print("")
            print("")
            print(f"Motion torture, f={f}")
            grbl.move(z=100, f=1000)
            for i in range(30):
                # Corner
                grbl.move(t=-34.827, p=-48.867, f=f)
                # Wafer station
                grbl.move(t=-21.138, p=-128.760, f=f)
                print("Error % 4u" % (i,))
                for i in range(3):
                    time.sleep(1.2)
                    pos_new = ra.grbl_get_pos_scara()
                    dt = -21.138 - pos_new['t_encoder']
                    dp = -128.760 - pos_new['p_encoder']
                    print("  t=%0.3f, p=%0.3f" % (dt, dp))

        def home_at_loadlock():
            safely_get_to_loadlock(homing=True)

        def move_wafer_from_loadlock_to_loadport():
            safely_get_to_loadlock()
            
            # prepare to enter wafer holder
            # ra.move_pos({'z': 250}, f=100)
            grbl.move(z=100, f=1000)
            grbl.move(t=-21.138, p=-128.760, f=2000)
            grbl.move(z=25, f=1000)
            # into wafer holder
            grbl.move(t=-32.651, p=-112.039, f=2000)
            # up to grab wafer
            # 50 => not enough clearance for attachments on bottom :P
            grbl.move(z=80, f=1000)

            # start in corner
            grbl.move(t=-34.827, p=-48.867, f=500)
            grbl.move(t=-84.661, p=54.207, f=500)
            grbl.move(t=-86.638, p=80.420, f=500)
            # elbow tucked in deep
            grbl.move(t=-76.992, p=139.768, f=500)

            # now the big move
            grbl.move(t=24.434, p=134.055, f=500)
            # move to load port
            grbl.move(t=24.434, p=122.498, f=500)
            # and in
            # fixme
            ra.set_station("loadport")

        def move_wafer_from_loadport_to_loadlock():
            # safely_get_to_loadport()

            # clearance above wafer holder
            grbl.move(z=80, f=1000)

            # move to load port
            grbl.move(t=24.434, p=122.498, f=500)
            # near port tucked in
            grbl.move(t=24.434, p=134.055, f=500)


            # bulk move to corner
            grbl.move(t=-76.992, p=139.768, f=500)
            # get to corner itself
            grbl.move(t=-86.638, p=80.420, f=500)
            grbl.move(t=-84.661, p=54.207, f=500)
            grbl.move(t=-34.827, p=-48.867, f=500)

            # near wafer holder
            grbl.move(t=-21.138, p=-128.760, f=500)
            # into wafer holder
            grbl.move(t=-32.651, p=-112.039, f=500)
            # Set wafer down
            grbl.move(z=25, f=1000)
            # out of wafer holder
            grbl.move(t=-21.138, p=-128.760, f=2000)
            ra.set_station("loadlock")

        if 0:
            move_torture_test(f=2000)
            move_torture_test(f=5000)
            move_torture_test(f=12000)
            print("Debug break")
            return

        if 1:
            home_at_loadlock()
            move_wafer_from_loadlock_to_loadport()
            move_wafer_from_loadport_to_loadlock()


    except Exception as e:
        print("WARNING: exception")
        # ra.estop()
        raise
    print("Done")



main()
