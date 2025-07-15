"""
Parameter for CNC control
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
        def ticks_add(*a, **k):
            pass
        def ticks_ms():
            pass
        def ticks_diff():
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
    """Buffer object to for sending serial to grbl
       grbl can recv up to 128bytes at once so we can send before we get 'ok' """
    def __init__(self) -> None:
        self.max_buf = 128
        self.buflen = 0
        self.uart = _null # this has to be injected at grbl.update() as uart may not exist yet
        # self.gene = None       # this has to be injected at grbl.update()
        self.queue = []
        self.mt_buf = False  # set when we're emptying buffer, once buffer is mt we will next gene
        self.planner = 15  # size of grbl planner
        self.max_planner = 15
        self.buffer = 128  # size of grbl buffer ## for now I think that Iris loop is slower than GRBL's so we can't overrrun it by sending single commands
        self.num_sent = 0  # we must count the number of commands sent so we may wait til mtbuf is completed

    def send(self, cmd, mt_buf=False, newline=True):  # -> True|None:
        if newline:
            cmd += '\n'
        
        if mt_buf:
            self.mt_buf = True
            _continue = None
        
        if self.planner:
            self.planner -= 1
            self.num_sent += 1
            # ok to send
            self.uart(cmd)
            _continue = True
        else:
            print('buffer q', cmd)
            self.queue.append(cmd)
            _continue = None
        
        return _continue
    
    def ok(self):
        # we got 'ok' 
        self.num_sent -= 1
        if self.num_sent < 0:
            print('grbl buffer underrun something must have happened')
            self.num_sent = 0
        self.planner += 1
        if self.planner > self.max_planner:
            self.planner = self.max_planner   
              
        if self.queue:
            # print('checking planner', self.planner)
            if self.planner > 10: # let's try and give some time to buffer ok's
                # print('sending buffered')
                self.send(self.queue.pop(), newline=False)
                if not self.mt_buf:
                    return True
        else:
            if self.mt_buf and self.planner == self.max_planner:
                print('buf flushed')
                self.mt_buf = False
                return True

class Move:
    def __init__(self):
        pass
    def make(self, cmd, **k):
        order = {'cmd': cmd}
        order.update(k)
        return order
    def __call__(self, **k):
        return self.make('move', **k)
    def linear(self, **k):
        return self.make('move.linear', **k)
    def rapid(self, **k):
        return self.make('move.rapid', **k)
move = Move()      

class GRBL(Parameter):
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
        # todo add functions back in? should they be injected somehow else?
        super().__init__(iris=iris, name=name,  **k)
        self.uart: Parameter = UART
        self.buffer = Buffer()  # this is the buffer on the grbl board. buffer_size = 128 bytes
        self.state = 'alarm'
        self.queue = {}
        self.axes = OrderedDict()  # {'theta': GRBLAxis}
        
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
        
        #  self.f = functions  # example {'home_x', pid}
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
            'enable_motors': lambda *_: self.send_g('$ME'), 
            'feed_hold': lambda *_: self.send_g(b'!'), # TODO: probably handle this better?
            'send_raw_line': lambda line: self.send_g(line),
            'move.linear': self.move,
            'move.rapid': self.move,
            'move': self.move,
            'listdir': self.listdir,
            'mt_buf': self.mt_buf,
            'run': self.run,
        }
        
        self.bifrost = None
        if webserver_output:
            self.bifrost = True
            
        self.gene = Gene(iris=iris, bifrost=iris.bifrost, pid=69)
        self.scripts = {}  # scripts for Gene
        
        self.hbt_int = hbt
        self.next_hbt = utime.ticks_add(utime.ticks_ms(), self.hbt_int)
        self.webstuff = {'name': name, 'pid': self.pid, 'type': 'GRBL'}
        
    def update(self):
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
        self.axes_map = OrderedDict()
        for label, axis in self.axes.items():
            self.axes_map[label] = axis.name
        
        self.gene.register_functions(self, list(self.funcs.keys()), param_is_cnc=True)
        self.buffer.uart = self.uart

        runtime = sys.implementation
        # do not run async in pyscripts and other pythons
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return 
        self.buffer.send('$10=2\n') # add thing for extra debug from status query

        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())

    def gui(self):
        return {'name': self.name, 'pid': self.pid, 'axes': list(self.axes.keys()), 'type': 'GRBL'}
    
    def save(self):
        file = dict(
            tool_offset=self.tool_offset,
            tool_offsets=self.tool_offsets,
            work_offset=self.work_offset,
            work_offsets=self.work_offsets,
        )
        with open(f'grbl{self.pid}.json', 'w') as f:
            json.dump(file, f)
        
    def __call__(self, state: dict | JSON | bytes, gui=False):
        # example: {'cmd': function, 'data': argument} 
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
        return self.positions

    async def chk(self):
        while True:
            # do heartbeat, poll grbl
            if utime.ticks_diff(self.next_hbt, utime.ticks_ms()) <= 0:
                self.uart('?')  # this bypasses the buffer, grbl executes on recv
                self.next_hbt = utime.ticks_add(self.next_hbt, self.hbt_int)

            self.check_uart()
            await asyncio.sleep(0)
    
    def check_uart(self):
        while self.uart.any():
            msg = self.uart.readline()
            
            if msg == '':
                return

            if msg[0] == '<': # grbl info line
                self.parse_status(msg)

            elif msg == 'ok':
                if self.buffer.ok():
                    self.gene(None)
                return

            else:
                if self.iris.bifrost is not None:
                    self.iris.bifrost.send(self.pid, {'cmd': 'post', 'data': msg})

    def run(self, script: str | list):
        if isinstance(script, str):
            if script in self.scripts:
                self.gene.load(self.scripts[script])
            else:        
                self.gene.load(script)
        elif isinstance(script, dict):
            #TODO parse this better if there are more kwargs
            self.gene.load(script['script'])
        else:
            self.gene.load(script)

    def mt_buf(self):
        # print('mt_buf')
        self.buffer.send('G4 P.01', mt_buf=True)
        
    def move(self, order: dict):
        def linear(order):
            # example: {'cmd': 'move.linear', 'x': 5, 'y': None}
            
            if 'feed' in order:
                feed = str(order.pop('feed'))
            else:
                feed = self.default_feedrate
            feed = f'F{feed}'
            
            # clean empty values
            order = {axis: float(val) for axis, val in order.items() if val != ''}
            
            # apply offset
            for axis, val in order.items():
                order[axis] = val + self.work_offset[axis]
            
            line = ['G1']
            line.extend([f"{k.upper()}{v}" for k,v in order.items()])
            line.append(feed)
            
            line = ' '.join(line)

            self.state = 'run'
            # self.send_g(line)
            _continue = self.buffer.send(line)
            # if this is called by Gene then we want to return true so we may continue running    
            return _continue
        
        
        def rapid(order):
            # example: {'cmd': 'move.rapid', 'x': 5, 'y': None}
            
            if 'feed' in order:
                feed = str(order.pop('feed'))
            else:
                feed = self.default_feedrate
            feed = f'F{feed}'
            
            # clean empty values
            order = {axis: float(val) for axis, val in order.items() if val != ''}
            
            # apply offset
            for axis, val in order.items():
                order[axis] = val + self.work_offset[axis]
            
            line = ['G1']
            line.extend([f"{k.upper()}{v}" for k,v in order.items()])
            line.append(feed)
            
            line = ' '.join(line)

            self.state = 'run'
            # self.send_g(line)
            _continue = self.buffer.send(line)
            # if this is called by Gene then we want to return true so we may continue running    
            return _continue
        
        
        # example: {'cmd': 'move.linear', 'x': 5, 'y': None}
        if 'comment' in order:
            self.send_bf(order.pop('comment'))
        
        if order['cmd'] == 'move.linear':
            return linear(order)
        elif order['cmd'] == 'move.rapid':
            return rapid(order)

    def jog_button(self, order):
        val: float = order['val']  # distance to move
        dir: bool = order['dir']  # dir to move
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
        # this is an order
        # order.pop('cmd')
        name = order.pop('name')
        self.set_tool_offset(name, order)
    
    def set_tool_offset(self, name: str, vals: dict[str, float]):
        print('wrong one')
        self.tool_offsets[name] = vals
        self.send_bf({'cmd': 'set_tool_offset', 'data': self.tool_offsets})
    
    
    def _set_work_offset(self, order):
        # this is an order
        # order.pop('cmd')
        name = order.pop('name')
        self.set_work_offset(name, order)
    
    def set_work_offset(self, name: str, vals: dict[str, float]):
        self.work_offsets[name] = vals
        self.save()
        self.send_bf({'cmd': 'set_work_offset', 'data': self.work_offsets})
    
    def change_work_offset(self, name:str|dict):
        # name is the key for the work offset
        if isinstance(name, dict): # this is an order
            name = name['data']
        self.work_offset = name
        self.send_bf({'cmd': 'change_work_offset', 'data': name})
    
    def change_tool_offset(self, name:str|dict):
        # name is the key for the work offset
        if isinstance(name, dict): # this is an order
            name = name['data']
        self.tool_offset = name
        self.send_bf({'cmd': 'change_tool_offset', 'data': name})
    
    def machine(self, raw_cmd: dict):
        '''portal to GRBL machine for setting and getting parameters
        {cmd: "machine", action: "set", command: "$/axes/x/steps_per_mm", value: 100}
        '''
        command = raw_cmd['command']
        if raw_cmd['action'] == 'set':
            command += f"={raw_cmd['value']}"
        print(command)
                
        self.buffer.send(command)
    
    def home(self, axis):  # home axis with endstop grbl
        self.send_g('$H{}'.format(axis.upper()))
        
    def jog(self, axis, dir):  # not yet implemented
        destination = 1000.0
        ax = axis.upper()
        if dir == 'minus':
            destination = -destination
        self.send_g(f'$J={ax}{destination} F500')
        
    def send_g(self, cmd):  # send line to grbl over serial 
        self.buffer.send(cmd)
                    
    def send_bf(self, msg: str):  # send message to self terminal bifrost
        self.iris.bifrost.send(self.pid, msg)

    def listdir(self, *args, **kwargs):
        files = os.listdir()
        if 'sd' in files:
            files.extend([f'sd/{file}' for file in os.listdir('sd')])
        files = {'cmd': 'populate_files', 'data': files}
        self.iris.bifrost.send(self.pid, files)
        
    def parse_status(self, msg: str) -> None:
        def status_str() -> str:
            l = [self.status['state']]
            for axis, pos in self.positions.items():
                l.append(f'{axis}{round(pos, 3)}')
            l.append(self.status['limits'])
            return ' '.join(l)
        
        # example: <Idle|MPos:0.000,0.000,0.000|FS:0,0>
        msg = msg.strip('<>').split('|')
        self.status['state'] = msg[0]
        mpos = msg[1][5:].split(',')  # remove Mpos:
        
        for i, axis in enumerate(self.axes):
            self.status['MPos'][axis] = float(mpos[i])
            self.positions[axis] = self.status['MPos'][axis] - self.offset[axis]
            
        # self.status['limits'] = msg[3]
        # print(status_str())
        if self.bifrost:
            msg = {'cmd': 'status'}
            msg.update(self.positions)
            msg['state'] = self.status['state']
            self.send_bf(msg)
        
# $/axes/x/acceleration_mm_per_sec2=100







    