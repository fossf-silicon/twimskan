"""
GRBL CNC Control Module

This module provides an object-oriented interface to a GRBL-controlled CNC machine,
facilitating real-time motion control, status monitoring, and serial communication
through UART. It integrates with the `floe` system, `Gene` sequencing, and the 
`Iris` runtime for scripting and web interfacing.

Key Components:
---------------
- `Buffer`: Manages the GRBL planner and serial buffer to avoid overflow. Implements a command queue and supports delayed execution.
- `Move`: Helper class to create motion command dictionaries for linear and rapid movement.
- `GRBL`: Core class that inherits from `Parameter`. Interfaces with hardware, manages axes, maintains tool/work offsets, and registers CNC-related commands for Gene execution.

Major Features:
---------------
- Axis control (`x`, `y`, `z`, `a`, `b`, `c`) with support for tool and work coordinate offsets.
- Serialized command buffering to maintain planner integrity and synchronization with GRBL.
- Motion command execution (`move.linear`, `move.rapid`, jogging, homing).
- JSON-based configuration persistence.
- Real-time status parsing and dispatch via bifrost/web interface.
- Integration with coroutine-based update loops for embedded targets (e.g., MicroPython).
- Compatibility with environments that lack certain modules like `utime` or `uasyncio`.

Usage:
------
The `GRBL` class is designed to be instantiated with an `Iris` runtime and a UART send function.
After initialization and a call to `update()`, the object is ready to accept structured
motion or command instructions, either via the `__call__()` interface or by directly invoking
methods like `move()`, `home()`, `machine()`, etc.

Example:
--------
    grbl = GRBL(iris=iris_instance, UART=my_uart_func)
    grbl.update()
    grbl({'cmd': 'move.linear', 'x': 10.0, 'y': 5.0, 'feed': 200})
"""

# import floe
from Parameter import Parameter
from floe import make_var
from Gene import Gene
from collections import OrderedDict, deque 
import json, os, sys

try: 
    import utime
except:
    class Utime:
        def __init__(self):
            pass
        def ticks_add(self, *a, **k):
            pass
        def ticks_ms(self):
            pass
        def ticks_diff(self):
            pass
    utime = Utime()
        
try:
    import uasyncio as asyncio
except:
    import asyncio
from floe import FP
from iris import Iris

JSON = str

def _null(a):
    pass

class Buffer:
    """Manages GRBL's planner and UART buffer.

    Handles command queuing, sending, and flush tracking based on planner size.
    Prevents planner overflow and enables smooth streaming to GRBL.
    """
    def __init__(self) -> None:
        """Initialize the buffer and planner queue."""
        self.max_buf = 128
        self.buflen = 0
        self.uart = _null  # To be injected by GRBL.update()
        self.queue = []
        self.mt_buf = False  # Indicates flushing state
        self.planner = 15
        self.max_planner = 15
        self.buffer = 128
        self.num_sent = 0

    def send(self, cmd, mt_buf=False, newline=True):
        """Queue or transmit a G-code command to GRBL.

        Args:
            cmd (str): Command string to send.
            mt_buf (bool): Whether to flush buffer after this command.
            newline (bool): Whether to append a newline character.

        Returns:
            bool | None: True if sent immediately, None if queued.
        """
        if newline:
            cmd += '\n'
        if mt_buf:
            self.mt_buf = True
            _continue = None
        if self.planner:
            self.planner -= 1
            self.num_sent += 1
            self.uart(cmd)
            _continue = True
        else:
            print('buffer q', cmd)
            self.queue.append(cmd)
            _continue = None
        return _continue

    def ok(self):
        """Process a GRBL 'ok' message.

        Updates planner status, checks for queued commands, and flushes if needed.

        Returns:
            bool | None: True if flush completed, otherwise None.
        """
        self.num_sent -= 1
        if self.num_sent < 0:
            print('grbl buffer underrun something must have happened')
            self.num_sent = 0
        self.planner += 1
        if self.planner > self.max_planner:
            self.planner = self.max_planner
        if self.queue:
            if self.planner > 10:
                self.send(self.queue.pop(), newline=False)
                if not self.mt_buf:
                    return True
        else:
            if self.mt_buf and self.planner == self.max_planner:
                print('buf flushed')
                self.mt_buf = False
                return True

class Move:
    """Helper class to create move command dictionaries for linear and rapid motion."""
    def __init__(self):
        pass

    def make(self, cmd, **k):
        """Create a dictionary describing a motion command.

        Args:
            cmd (str): Base command name (e.g., 'move.linear').
            **k: Axis values and feedrate.

        Returns:
            dict: Complete move command dictionary.
        """
        order = {'cmd': cmd}
        order.update(k)
        return order

    def __call__(self, **k):
        """Shorthand for a standard move."""
        return self.make('move', **k)

    def linear(self, **k):
        """Create a linear (G1) motion command."""
        return self.make('move.linear', **k)

    def rapid(self, **k):
        """Create a rapid (G0-like) motion command."""
        return self.make('move.rapid', **k)

move = Move()

class GRBL(Parameter):
    """Main controller class for interfacing with a GRBL-based CNC machine.

    Inherits from Parameter and provides full CNC control, status handling,
    jogging, homing, tool/work offsets, and Gene scripting.
    """
    standards = ('x','y','z','a','b','c')

    def __init__(self, *, 
                 name: str='fake_grbl',
                 iris: Iris, 
                 UART: FP=lambda x: print(x),
                 hbt:int=1000, 
                 x:FP | None=None, 
                 y:FP | None=None, 
                 z:FP | None=None, 
                 a:FP | None=None, 
                 b:FP | None=None, 
                 c:FP | None=None, 
                 webserver_output: bool=True,
                 **k):
        """Initialize the GRBL control interface.

        Args:
            name (str): Controller name.
            iris (Iris): Execution context for Gene and RPC.
            UART (callable): Function for writing serial data to GRBL.
            hbt (int): Heartbeat polling interval (ms).
            x...c (FP | None): Optional axis references.
            webserver_output (bool): Enable web status reporting.
            **k: Additional keyword arguments passed to Parameter.
        """
        super().__init__(iris=iris, name=name,  **k)
        self.uart: Parameter = UART
        self.buffer = Buffer()
        self.state = 'alarm'
        self.queue = {}
        self.axes = OrderedDict()
        self.axes_lookup = None  # will be populated on update
        
        for label, axis in zip(self.standards, (x,y,z,a,b,c)):
            if axis is not None:
                self.axes[label] = axis

        self.work_offset = 'machine'
        self.work_offsets = OrderedDict(
            machine={axis: 0 for axis in self.axes},
            board_offset={axis: 0 for axis in self.axes}
        )

        self.tool_offset = 'default'
        self.tool_offsets = OrderedDict()

        self.positions = {axis: 0 for axis in self.axes}
        self.default_feedrate = '500'
        self.rapid_feedrate = '3500'

        self.status = {
            'state': 'Sleep',
            'MPos': {axis: 0 for axis in self.axes},
            'limits': ''
        }

        self.funcs = {
            'home_x': lambda *_: self.home('x'),
            'home_y': lambda *_: self.home('y'),
            'home_z': lambda *_: self.home('z'),
            'home_a': lambda *_: self.home('a'),
            'home_b': lambda *_: self.home('b'),
            'home_c': lambda *_: self.home('c'),
            'home': self.home,
            'term': lambda line: self.buffer.send(line['msg']),
            'machine': self.machine,
            'set_work_offset': self._set_work_offset,
            'change_work_offset': self.change_work_offset,
            'set_tool_offset': self._set_tool_offset,
            'change_tool_offset': self.change_tool_offset,
            'unlock': lambda *_: self.send_g('$X'),
            'disable_motors': lambda *_: self.send_g('$MD'),
            'jog_cancel': lambda *_: self.send_g(b'\x85'),
            'jog_button': self.jog_button,
            'get_status': lambda *_: self.uart('?'),
            'enable_motors': self.enable_motors,
            'feed_hold': lambda *_: self.send_g(b'!'),
            'send_raw_line': lambda line: self.send_g(line),
            'move.linear': self._move,
            'move.rapid': self._move,
            'move': self._move,
            'listdir': self._listdir,
            'mt_buf': self.mt_buf,
            'run': self.run,
            'feed_hold': self.feed_hold,
            'resume': self.resume,
        }

        self.bifrost = None
        if webserver_output:
            self.bifrost = True

        self.gene = Gene(iris=iris, bifrost=iris.bifrost, pid=69)
        self.scripts = {}

        self.hbt_int = hbt
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)
        self.webstuff = {'name': name, 'pid': self.pid, 'type': 'GRBL'}

                
    def update(self):
        """Loads config from disk, refreshes axes, registers Gene functions."""
        super().update()
        axes = OrderedDict()
        for label, axis in self.axes.items():
            axes[label] = self.iris.p[axis.pid]

        
        if f'grbl{self.pid}.json' in os.listdir():    
            with open(f'grbl{self.pid}.json', 'r') as f:
                file = json.load(f)
                self.work_offset = file['work_offset']
                self.work_offsets = file['work_offsets']
                self.tool_offset = file['tool_offset']
                self.tool_offsets = file['tool_offsets']

        self.axes = axes
        self.axes_lookup = axes = {axis.name: alias for alias, axis in self.axes.items()}
        
        self.axes_map = OrderedDict()
        for label, axis in self.axes.items():
            self.axes_map[label] = axis.name

        self.gene.register_functions(self, list(self.funcs.keys()), param_is_cnc=True)
        self.buffer.uart = self.uart

        runtime = sys.implementation
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return
        self.buffer.send('$10=2\n')

        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())

    def gui(self):
        """Returns metadata dictionary for web frontend."""
        return {'name': self.name, 'pid': self.pid, 'axes': list(self.axes.keys()), 'type': 'GRBL'}

    def enable_motors(self, axis: str=""):
        if not axis:
            self.send_g('$ME')  # turn off all motors
        else:
            if axis in self.axes_lookup:
                this_axis = self.axes_lookup[axis].upper()
                self.send_g(f'$ME={this_axis}')

    def disable_motors(self, axis: str=""):
        if not axis:
            self.send_g('$MD')  # turn off all motors
        else:
            if axis in self.axes_lookup:
                this_axis = self.axes_lookup[axis].upper()
                self.send_g(f'$MD={this_axis}')


    def save(self):
        """Writes current tool and work offset configuration to disk."""
        file = dict(
            tool_offset=self.tool_offset,
            tool_offsets=self.tool_offsets,
            work_offset=self.work_offset,
            work_offsets=self.work_offsets,
        )
        with open(f'grbl{self.pid}.json', 'w') as f:
            json.dump(file, f)

    def __call__(self, state: dict | JSON | bytes, gui=False):
        """Processes incoming JSON commands, dispatching to internal functions."""
        print('grbl', state)
        if isinstance(state, bytes):
            state = state.decode('utf-8')
        if isinstance(state, str):
            state = json.loads(state)
        cmd = state.pop('cmd')
        if state != {}:
            return self.funcs[cmd](state)
        else:
            return self.funcs[cmd]()

    def get_pos(self, *, kinematics='cartesian'):
        """Returns dictionary of current axis positions.
        If other kinematics from child classes are available they may be requested
        These positions are the ones from the grbl machine.
        """
        return self.positions

    async def chk(self):
        """Asynchronous coroutine that sends periodic status requests to GRBL."""
        while True:
            if utime.ticks_diff(self.next_hbt, utime.ticks_ms()) <= 0:
                self.uart('?')
                self.next_hbt = utime.ticks_add(self.next_hbt, self.hbt_int)
            self._check_uart()
            await asyncio.sleep(0)

    def _check_uart(self):
        """Parses incoming UART data and handles GRBL output messages."""
        while self.uart.any():
            msg = self.uart.readline()
            if msg == '':
                return
            if msg[0] == '<':
                self.parse_status(msg)
            elif msg == 'ok':
                if self.buffer.ok():
                    self.gene(None)
                return
            else:
                if self.iris.bifrost is not None:
                    self.iris.bifrost.send(self.pid, {'cmd': 'post', 'data': msg})

    def run(self, script: str | list):
        """Executes a script using the Gene engine.

        Args:
            script (str | list | dict): The script to load and run.
        """
        if isinstance(script, str):
            if script in self.scripts:
                self.gene.load(self.scripts[script])
            else:
                self.gene.load(script)
        elif isinstance(script, dict):
            self.gene.load(script['script'])
        else:
            self.gene.load(script)

    def mt_buf(self):
        """Send a small delay command and flag buffer flush for synchronization."""
        self.buffer.send('G4 P.01', mt_buf=True)

    def move(self, *, x=None,y=None,z=None,a=None,b=None,c=None,f=None):
        order = {'cmd': 'move'}
        axes = {axis: val for axis, val in zip('xyzabcf', [x,y,z,a,b,c,f]) if val is not None}
        if not axes:
            return
        order.update(axes)
        return order
        
    def _move(self, order: dict):
        """Dispatches move command to GRBL.

        Supports linear and rapid moves using G-code commands.
        """
        def linear(order):
            if 'f' in order:
                feed = str(order.pop('f'))
            else:
                feed = self.default_feedrate
            feed = f'F{feed}'
            order = {axis: float(val) for axis, val in order.items() if val != ''}
            for axis, val in order.items():
                order[axis] = val + self.work_offset[axis]
            line = ['G1']
            line.extend([f"{k.upper()}{v}" for k,v in order.items()])
            line.append(feed)
            line = ' '.join(line)
            self.state = 'run'
            return self.buffer.send(line)

        def rapid(order):
            if 'f' in order:
                feed = str(order.pop('f'))
            else:
                feed = self.default_feedrate
            feed = f'F{feed}'
            order = {axis: float(val) for axis, val in order.items() if val != ''}
            for axis, val in order.items():
                order[axis] = val + self.work_offset[axis]
            line = ['G1']
            line.extend([f"{k.upper()}{v}" for k,v in order.items()])
            line.append(feed)
            line = ' '.join(line)
            self.state = 'run'
            return self.buffer.send(line)

        if 'comment' in order:
            self.send_bf(order.pop('comment'))
        if order['cmd'] == 'move.linear':
            return linear(order)
        elif order['cmd'] == 'move.rapid':
            return rapid(order)

    def jog_button(self, order):
        """Handles jog movement for a button input event.

        Args:
            order (dict): Includes 'val', 'dir', 'axis'.
        """
        val: float = order['val']
        dir: bool = order['dir']
        axis:str = order['axis']
        mapped_axis = None
        for _axis, mapped in self.axes_map.items():
            if mapped == axis:
                mapped_axis = _axis
        if dir:
            pos = self.positions[mapped_axis] + val
        else:
            pos = self.positions[mapped_axis] - val
        move = {axis: pos, 'feed': 500}
        self.move(move)

    def _set_tool_offset(self, order):
        """Helper to set tool offset from RPC order."""
        name = order.pop('name')
        self.set_tool_offset(name, order)

    def set_tool_offset(self, name: str, vals: dict[str, float]):
        """Sets and reports the tool offset for a named configuration."""
        self.tool_offsets[name] = vals
        self.send_bf({'cmd': 'set_tool_offset', 'data': self.tool_offsets})

    def _set_work_offset(self, order):
        """Helper to set work offset from RPC order."""
        name = order.pop('name')
        self.set_work_offset(name, order)

    def set_work_offset(self, name: str, vals: dict[str, float]):
        """Sets and saves work offsets for named configuration."""
        self.work_offsets[name] = vals
        self.save()
        self.send_bf({'cmd': 'set_work_offset', 'data': self.work_offsets})

    def change_work_offset(self, name:str|dict):
        """Activates a different work offset configuration."""
        if isinstance(name, dict):
            name = name['data']
        self.work_offset = name
        self.send_bf({'cmd': 'change_work_offset', 'data': name})

    def change_tool_offset(self, name:str|dict):
        """Activates a different tool offset configuration."""
        if isinstance(name, dict):
            name = name['data']
        self.tool_offset = name
        self.send_bf({'cmd': 'change_tool_offset', 'data': name})

    def feed_hold(self):
        """Send GRBL command to pause motion (feed hold)."""
        self.uart('!')

    def resume(self):
        """Send GRBL command to resume from feed hold."""
        self.uart('~')

    def machine(self, raw_cmd: dict):
        """Send direct GRBL machine configuration commands.

        Args:
            raw_cmd (dict): Must contain 'command' and optionally 'value' and 'action'.
        """
        command = raw_cmd['command']
        if raw_cmd['action'] == 'set':
            command += f"={raw_cmd['value']}"
        self.buffer.send(command)

    def home(self, axis):
        """Home the specified axis using GRBL's endstop routine."""
        self.send_g('$H{}'.format(axis.upper()))

    def jog(self, axis: str, dir):
        """Jog an axis in specified direction by a fixed amount.

        Args:
            axis (str): Axis label.
            dir (str): 'plus' or 'minus'.
        """
        destination = 1000.0
        ax = axis.upper()
        if dir == 'minus':
            destination = -destination
        self.send_g(f'$J={ax}{destination} F500')

    def send_g(self, cmd):
        """Send G-code line to GRBL via the buffer.

        Args:
            cmd (str): G-code line or binary GRBL command.
        """
        self.buffer.send(cmd)

    def send_bf(self, msg: str, post=False):
        """Send message to Bifrost terminal for frontend display."""
        if post:
            self.iris.bifrost.post(msg)
        else:
            self.iris.bifrost.send(self.pid, msg)

    def _listdir(self, *args, **kwargs):
        """List files in root and optional SD card directory."""
        files = os.listdir()
        if 'sd' in files:
            files.extend([f'sd/{file}' for file in os.listdir('sd')])
        files = {'cmd': 'populate_files', 'data': files}
        self.iris.bifrost.send(self.pid, files)

    def parse_status(self, msg: str) -> None:
        """Parse GRBL status line and update internal state.

        Args:
            msg (str): Status string from GRBL (e.g., <Idle|MPos:...>).
        """
        def status_str() -> str:
            l = [self.status['state']]
            for axis, pos in self.positions.items():
                l.append(f'{axis}{round(pos, 3)}')
            l.append(self.status['limits'])
            return ' '.join(l)

        msg = msg.strip('<>').split('|')
        self.status['state'] = msg[0]
        mpos = msg[1][5:].split(',')
        for i, axis in enumerate(self.axes):
            self.status['MPos'][axis] = float(mpos[i])
            self.positions[axis] = self.status['MPos'][axis] - self.offset[axis]
        if self.bifrost:
            msg = {'cmd': 'status'}
            msg.update(self.positions)
            msg['state'] = self.status['state']
            self.send_bf(msg)
