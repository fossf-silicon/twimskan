#!/usr/bin/env python3
"""
Evezor robot arm
Ours is named "Jean" by the factory

WARNING: StdIn on micropython side was modified to make parsing easier
<return>reply</return>


angles
t: theta
p: phi ("theta2")
z: Evezor z axis
r: GRBL fork ("theta3")
Special:
f: feed



TODO: generate new homing point near load station
do this when installing / checking front shield which we'll need to be more careful about
(possibly clear right now but unsure)
"""
import time
import sys

import serial
from pexpect_serial import SerialSpawn
import ast
from collections import OrderedDict
import datetime
from woodpecker import Woodpecker
import glob
from uscope.util import add_bool_arg

# ignore woodpecker moves to try arm w/o it
STUB_WOODPECKER = 0

def printt(format, *args, **kwargs):
    print(str(datetime.datetime.now().isoformat()) + ": " + format, *args, **kwargs)

class GrblTimeout(Exception):
    pass

class EncoderFault(Exception):
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

def within_max_axis_error(pos_want, pos_got, tolerance=1, verbose=True):
    for k in pos_want.keys():
        delta = pos_got[k] - pos_want[k]
        verbose and printt("within_max_axis_error: check %s: want %s, got %s, want delta %s < tolerance %s" % (k, pos_want[k], pos_got[k], delta, tolerance))
        delta = abs(delta)
        if delta > tolerance:
            verbose and printt("  within_max_axis_error: axis fail")
            return False
        verbose and printt("  within_max_axis_error: axis ok")
        verbose and printt("  within_max_axis_error: ok")
    return True

def pos2tpz(pos):
    """
    Filter out encoder, f, etc to give clean position dict
    """
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

    # Encoders have an accuracy of 0.8 degrees per datasheet
    # Use them for rough crash detection but don't rely on them for actual position
    # We could sweep + make calibration map if we really needed something better
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
        if within_max_axis_error(pos_want, pos_final, tolerance=2.0):
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

        woodpecker_pos = None
        # hack
        if 'r' in kwargs:
            if not STUB_WOODPECKER:
                assert self.ra.woodpecker
                woodpecker_pos = kwargs['r']
                self.ra.woodpecker.theta3.move(woodpecker_pos, block=block)
            del kwargs['r']

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
            if woodpecker_pos is not None:
                self.ra.woodpecker.theta3.wait_idle()
  
        else:
            assert 0, "everything should block right now"



class RobotArm:
    def __init__(self, woodpecker=None, port = '/dev/ttyUSB0', check_encoder_fault=True):
        print("RobotArm: connecting to %s" % port)
        self.serial = serial.Serial(port, 115200, timeout=0.01)
        self.ss = SerialSpawn(self.serial)
        self.grbl = GrblWrap(self)
        self.station = None
        # Reduce feed rates when have wafer
        # Default to true to be safer
        self.has_wafer = True

        if woodpecker is None and len(glob.glob("/dev/ttyUSB*")) == 2:
            print("RobotArm: auto-connecting woodpecker")
            woodpecker = Woodpecker()
        self.woodpecker = woodpecker

        if check_encoder_fault:
            self.check_encoder_fault()

    def check_encoder_fault(self):
        pos = self.grbl_get_pos_scara()
        if pos['t'] == 0 and pos['p'] == 0 and pos['z'] == 0:
            raise EncoderFault("Encoders are reading all 0s. Manually reset encoder board to fix")


    def set_has_wafer(self, val):
        self.has_wafer = val

    def command(self, s):
        verbose = False
        # print("arm sending", s)

        # this will poison controller
        # arm sending grbl.move(f=None, p=135.549, r=-62, t=16.941)
        if s.find("r=") >= 0:
            print("arm sending", s)
            raise ValueError("probably bad command")

        verbose and print("Sending", s)
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

    def home(self, home_z=None):
        print("Startup homing sequence")
        self.force_user_move_to_loadport()

        orig_pos_scara = self.grbl_get_pos_scara()
        # t / p are a bit safe to do automatically 
        if orig_pos_scara['z'] == 0.0 or home_z:
            # assert 0, "z not homed (probably). Home before continuing"
            print("Need to home Z")
            print("Ensure is clear")
            input("Press Enter to continue...")
            print("Homing z...")
            self.home_z(block=True)
            print("Rough homing t...")
            self.home_t(block=True)
            print("Rough homing p...")
            self.home_p(block=True)
            print("Power up homing complete")
            self.home_z(block=True)
        self.home_at_loadport()

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
            self.wait_idle(timeout=120)

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


    """
    **********************************************************************
    High level functions
    Specific to our environment
    **********************************************************************
    """

    def home_at_point(self, position):
        ra = self
        grbl = ra.grbl

        """
        High level notes:
        -Home once to get roughly in position, then another once we are closer to there => more reliable
        -Resetting stepper pulse count makes positioning more reliable
        -Encoders and steps are not aligned. But try to always do the same position for best consistency
        -Many sensors take a while to flush through the system
        """
        print("move to homing position")

        def move_homing1(check):
            grbl.move(f=2000, check=check, **position)
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

    def auto_f(self, f):
        if f is None:
            if self.has_wafer:
                f = 500
            else:
                f = 2000
        return f



    """
    *****************************************************************************
    Load port
    *****************************************************************************
    """


    def move_loadport_final_approach(self, f=None, check=True):
        """
        Fork right in front of but not in the load port
        """
        print("move_loadport_final_approach()")
        self.grbl.move(t=17.227, p=137.219, r=-64, f=f, check=check)

    def get_loadport_final_approach_pos(self):
        return {'t':17.227, 'p':137.219}

    def pickup_wafer_loadport(self):
        """
        NOTE: forks won't fit to intended location
        set on surface instead
        30.476
        114.851

        z=30 below wafer
        z=20 below surface. not needed but safer for testing
        z=50 well cleared
        """
        print("pickup_wafer_loadport()")
        # Set expected z height
        self.grbl.move(z=20)
        # move in
        self.grbl.move(t=28.630, p=118.081)
        # pick up
        self.grbl.move(z=50)
        self.has_wafer = True

    def place_wafer_loadport(self):
        """
        Arm already holding wafer
        """
        print("place_wafer_loadport()")
        # Set expected z height
        self.grbl.move(z=50)
        # move in
        self.grbl.move(t=28.630, p=118.081)
        # Let go of it
        self.grbl.move(z=20)
        self.has_wafer = False

    def safely_get_to_loadport(self, homing=False):
        ra = self
        grbl = ra.grbl

        print("")
        print("")
        print("")
        print("safely_get_to_loadport()")
        if homing:
            print("Rough position sync")
            ra.home_p(block=True)
            ra.home_t(block=True)
        print("Checking initial arm position to move to loadlock")
        start = ra.grbl_get_pos_scara()
        # are we by the wafer stations?
        f = None
        # FIXME: proably need more navigation logic
        # Or maybe we just fail to home for now if its not in a very specific range?
        # microscope uses ~-17

        """
        Load port coordiantes
            self.grbl.move(t=20.215, p=133.616, r=-62, f=f, check=check)
        Microscope coordiantes
            grbl.move(t=-17.732, p=104.722, z=20.1, r=0)
            grbl.move(t=5.955, p=83.408, r=0)
        Loadlock coordinates
            self.grbl.move(t=-21.138, p=-128.760, r=fixme, f=f, check=check)
            self.grbl.move(t=-34.827, p=-48.867)
        """
        # load port or microscope
        if start['t'] > 0 and start['p'] > 0 or start['t'] < 0 and start['p'] > 0:
            print("Starting by user load/unload port / microscope half")
            grbl.move(z=100, f=1000, check=not homing)
            # now the big move
            # grbl.move(t=24.434, p=134.055, f=f, check=not homing)
            # move to load port
            self.move_loadport_final_approach(f=f, check=not homing)
        # load lock
        elif start['t'] < 0 and start['p'] < 0:
            print("Starting closer to TwimSkan load lock half")
            # corner is generally a safe move
            grbl.move(z=100, f=1000, check=not homing)
            # Drop last as we'll (optionally) home before moving there
            self.move_from_loadlock_to_loadport(drop_last=True)
        else:
            assert 0, ("Can't identify starting position", start)


        print("Rough move complete")
        # finally to station idle positon
        if homing:
            # WARNING: if you change this coordinate it has massive implications
            # Everything is calibrated from this
            self.home_at_point({'t':20, 'p':130})

        print("Move to final position")
        # move to load port
        self.move_loadport_final_approach(f=f, check=not homing)
        print("")
        print("")
        print("")

    def home_at_loadport(self):
        self.safely_get_to_loadport(homing=True)
        if self.woodpecker:
            self.woodpecker.theta3.home_lazy()


    def force_user_move_to_loadport(self):
        """
        Rather than handle all of the differnet cases
        Check if we are within spec
        If so press enter and lock position once we are there
        """
        print("")
        print("")
        print("")
        print("Verifying we are starting near the load port")
        desired_pos = self.get_loadport_final_approach_pos()
        print("Need arm at %s" % (format_scara_pos(desired_pos),))
        self.grbl_enable_motors()
        current_pos = encoder2pos(self.grbl_get_pos_scara())
        tolerance = 5
        if within_max_axis_error(desired_pos, current_pos, verbose=True, tolerance=tolerance):
            print("Position: ok")
        else:
            print("Position: needs adjustment. Disabling motors")
            self.grbl_disable_motors()
            while True:
                current_pos = encoder2pos(self.grbl_get_pos_scara())
                # prints stuff
                if within_max_axis_error(desired_pos, current_pos, verbose=True, tolerance=tolerance):
                    print("In spec! Don't move it")
                    input("Press Enter to lock")
                    self.grbl_enable_motors()
                    if within_max_axis_error(desired_pos, current_pos, verbose=True, tolerance=tolerance):
                        print("Verified position locked")
                        break
                    else:
                        print("Lost position :( Please re-try")
                        self.grbl_disable_motors()
                time.sleep(0.5)

    """
    *****************************************************************************
    Load lock
    *****************************************************************************
    """

    def move_loadlock_final_approach(self, f=None, check=True):
        """
        Fork right in front of but not in the load lock
        """
        print("move_loadlock_final_approach()")
        self.grbl.move(t=-21.138, p=-128.760, r=58, f=f, check=check)

    def move_loadlock_corner(self, f=None, check=True):
        """
        The cell corner near the load lock
        Generally a good clearance position as not a lot of stuff there
        """
        print("move_loadlock_corner()")
        self.grbl.move(t=-34.827, p=-48.867)

    # def safely_get_to_loadlock(self, homing=False):
    def safely_get_to_loadlock(self):
        """
        """
        ra = self
        grbl = ra.grbl
        #assert not homing
        homing = False

        print("")
        print("")
        print("")
        #if homing:
        #    print("Rough position sync")
        #    ra.home_p(block=True)
        #    ra.home_t(block=True)
        print("Checking initial arm position to move to loadlock")
        start = ra.grbl_get_pos_scara()
        # are we by the wafer stations?
        if start['t'] > 0:
            # phi folded over sharpy for tight space over there
            assert start['p'] > 0
            print("Starting by user load/unload port")
            # Reverse earlier moves
            grbl.move(z=100, f=1000, check=not homing)
            # Drop last as we'll (optionally) home before moving there
            self.move_from_loadport_to_loadlock(f=2000, check= not homing, drop_last=True)
        else:
            print("Starting closer to TwimSkan load lock")
            # corner is generally a safe move
            grbl.move(z=100, f=1000)
            self.move_loadlock_corner(f=2000, check=not homing)
            print("first move complete")
        # finally to station idle positon
        #if homing:
        #    self.home_at_point({'t':-20, 'p':-120})

        print("Move to final position")
        self.move_loadlock_final_approach()
        print("")
        print("")
        print("")

    def pickup_wafer_loadlock(self):
        """
        Must do final approach first
        """
        grbl = self.grbl
        # Get under wafer
        grbl.move(z=25, f=1000)
        # into wafer holder
        grbl.move(t=-34.321, p=-111.863, f=2000)
        # up to grab wafer
        # 50 => not enough clearance for attachments on bottom :P
        grbl.move(z=80, f=1000)
        self.has_wafer = True


    def place_wafer_loadlock(self):
        """
        Arm already holding wafer
        Loadlock in position
        """
        grbl = self.grbl
        grbl.move(z=80, f=1000)
        # into wafer holder
        grbl.move(t=-33.970, p=-112.434, f=2000)
        # Set wafer down
        grbl.move(z=25, f=1000)
        self.has_wafer = False
        # out of wafer holder
        self.move_loadlock_final_approach()




    """
    *****************************************************************************
    Microscope
    *****************************************************************************
    """

    def safely_get_to_microscope(self):
        grbl = self.grbl
        print("safely_get_to_microscope()")
        # near by
        self.safely_get_to_loadport()
        # Just before microscope
        grbl.move(z=80, r=0)
        grbl.move(t=-17.732, p=104.722, r=0)

    def enter_microscope(self):
        print("enter_microscope()")
        grbl = self.grbl
        grbl.move(z=20.1, r=0)
        # In
        grbl.move(t=5.955, p=83.408, r=0)

    def exit_microscope(self):
        print("exit_microscope()")
        grbl = self.grbl
        grbl.move(t=-17.732, p=104.722, r=0)
        grbl.move(z=80, r=0)


    """
    *****************************************************************************
    Transfer
    *****************************************************************************
    """


    def move_from_loadlock_to_loadport(self, f=None, check=True, drop_last=False):
        grbl = self.grbl
        f = self.auto_f(f)

        # assume we are starting at the loadlock
        # no need to move there?
        # do it for consistency
        grbl.move(t=-21.138, p=-128.760, f=f, check=check)

        # moves from move_wafer_from_loadlock_to_loadport()
        # start in corner
        grbl.move(t=-34.827, p=-48.867, f=f, check=check)
        grbl.move(t=-84.661, p=54.207, f=f, check=check)
        grbl.move(t=-86.638, p=80.420, f=f, check=check)
        # elbow tucked in deep
        grbl.move(t=-76.992, p=139.768, f=f, check=check)

        # now the big move
        grbl.move(t=24.434, p=134.055, f=f, check=check)
        # move to actual load port
        if not drop_last:
            # grbl.move(t=24.434, p=122.498, f=f, check=check)
            self.move_loadport_final_approach(f=f, check=check)


        """
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
        """

    def move_from_loadport_to_loadlock(self, f=None, check=True, drop_last=False):
        f = self.auto_f(f)

        # reverse of above moves
        grbl = self.grbl
        grbl.move(r=-90, f=80)
        # assert 0, "debug break"
        grbl.move(t=24.434, p=122.498, f=f, check=check)
        grbl.move(t=24.434, p=134.055, f=f, check=check)
        grbl.move(t=-76.992, p=139.768, f=f, check=check)
        grbl.move(t=-86.638, p=80.420, f=f, check=check)
        grbl.move(t=-84.661, p=54.207, f=f, check=check)
        # Corner
        # grbl.move(t=-34.827, p=-48.867, f=f, check=check)
        self.move_loadlock_corner(f=f, check=check)

        # Actual loadlock
        if not drop_last:
            # grbl.move(t=-21.138, p=-128.760, f=f, check=check)
            self.move_loadlock_final_approach(f=f, check=check)

        """
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
        """








    def move_wafer_from_loadlock_to_loadport(self):
        grbl = self.grbl

        self.safely_get_to_loadlock()
        # prepare to enter wafer holder
        # ra.move_pos({'z': 250}, f=100)
        # grbl.move(z=100, f=1000)
        self.pickup_wafer_loadlock()
        self.move_from_loadlock_to_loadport()
        self.place_wafer_loadport()
        self.set_station("loadport")

    def move_wafer_from_loadport_to_loadlock(self):
        grbl = self.grbl
        self.safely_get_to_loadport()
        # clearance above wafer holder
        self.pickup_wafer_loadport()
        self.move_from_loadport_to_loadlock()
        self.place_wafer_loadlock()
        self.set_station("loadlock")


    def move_torture_test(self, f=2000):
        ra = self
        grbl = ra.grbl
        print("")
        print("")
        print("")
        print(f"Motion torture, f={f}")
        ra.safely_get_to_loadlock()
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

    #def home_at_loadlock():
    #    safely_get_to_loadlock(homing=True)



def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Robot arm test app")
    add_bool_arg(parser, "--verbose", default=False, help="Verbose output")
    add_bool_arg(parser, "--home", default=True, help="Home at startup")
    add_bool_arg(parser, "--home-z", default=None, help="Force homing Z if homing")
    add_bool_arg(parser, "--teach-mode", help="")
    add_bool_arg(parser, "--test-loadport", help="")
    add_bool_arg(parser, "--test-loadlock", help="")
    add_bool_arg(parser, "--test-microscope", help="")
    add_bool_arg(parser, "--move-loadport-final-approach-wafer", help="")
    add_bool_arg(parser, "--pickup-wafer-loadport", help="You must do final approach first")
    add_bool_arg(parser, "--place-wafer-loadport", help="You must do final approach first")
    parser.add_argument("--t", type=float, default=None, help="")
    parser.add_argument("--p", type=float, default=None, help="")
    parser.add_argument("--z", type=float, default=None, help="")
    args = parser.parse_args()

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
    orig_pos_scara = ra.grbl_get_pos_scara()
    print("pos scara", orig_pos_scara)

    try:
        if args.teach_mode:
            print("Entering teach mode")
            ra.grbl_disable_motors()
            while True:
                printt(format_scara_pos(encoder2pos(ra.grbl_get_pos_scara())))
                time.sleep(0.1)

        if args.home:
            ra.home(home_z=args.home_z)

        if args.move_loadport_final_approach_wafer:
            print("Doing final approach")
            ra.move_loadport_final_approach()
            print("Wafer height")
            ra.grbl.move(z=20)

        if args.pickup_wafer_loadport:
            print("pickup_wafer_loadport()")
            ra.pickup_wafer_loadport()

        if args.place_wafer_loadport:
            print("place_wafer_loadport()")
            ra.place_wafer_loadport()


        if args.t is not None and args.p is not None:
            ra.grbl.move(t=args.t, p=args.p)
        elif args.t is not None:
            ra.grbl.move(t=args.t)
        elif args.p is not None:
            ra.grbl.move(p=args.p)
        if args.z is not None:
            ra.grbl.move(z=args.z)


        # loadport test
        # Including homing takes: 1:17
        if args.test_loadport:
            ra.set_has_wafer(False)
            print("Doing final approach")
            ra.move_loadport_final_approach()
            print("Picking up")
            time.sleep(5)
            ra.pickup_wafer_loadport()
            ra.move_loadport_final_approach()
            print("Placing")
            time.sleep(5)
            ra.place_wafer_loadport()
            ra.move_loadport_final_approach()

        # microscope test
        if args.test_microscope:
            ra.set_has_wafer(True)
            # safe starting point
            print("Going to loadport")
            ra.safely_get_to_microscope()
            print("Entering microscope")
            ra.enter_microscope()
            print("Exiting microscope")
            ra.exit_microscope()
            print("Going to loadport")
            ra.safely_get_to_loadport()

        if args.test_loadlock:
            # FIXME: workaround for bug
            # don't know source
            ra.woodpecker.theta3.home_lazy()
            ra.safely_get_to_loadlock()
            ra.woodpecker.theta3.home_lazy()
            print("Picking up wafer")
            ra.pickup_wafer_loadlock()
            print("Placing wafer")
            ra.place_wafer_loadlock()

    except Exception as e:
        print("WARNING: exception")
        # ra.estop()
        raise
    print("Done")


if __name__ == '__main__':
    main()
