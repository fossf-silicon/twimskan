"""
Parameter for CNC control
"""
# import floe
from parameters.Parameter import Parameter
from parameters.Gene import Gene
from collections import OrderedDict
import json, os
try: 
    import utime
except:
    import fakes.utime as utime
try:
    import uasyncio as asyncio
except:
    import asyncio
from floe import FP, Iris

JSON = str

class GRBL(Parameter):
    standards = ('x','y','z','a','b','c')
    
    def __init__(self, *, 
                 name: str,
                 iris: Iris, 
                 UART: FP,
                 hbt:int=1000, 
                 x:FP | None, 
                 y:FP | None, 
                 z:FP | None, 
                 a:FP | None, 
                 b:FP | None, 
                 c:FP | None, 
                 webserver_output: bool=False,
                 **k):
        # todo add functions back in? should they be injected somehow else?
        super().__init__(iris=iris, name=name,  **k)
        self.uart: Parameter = UART
        self.state = 'alarm'
        self.queue = {}
        self.axes = OrderedDict()  # {'theta': GRBLAxis}
        
        for label, axis in zip(self.standards, (x,y,z,a,b,c)):
            if axis is not None:
                self.axes[label] = axis
        
        self.offset = {axis: 0 for axis in self.axes}
        self.tool_offset = {axis: 0 for axis in self.axes}
        self.positions = {axis: 0 for axis in self.axes}
#         self.move = Move(self)
        self.default_feedrate = '500'
        self.rapid_feedrate = '1200'
        print(self.axes)
        
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
            'term': lambda line: self.send_g(line['msg']),
            'unlock': lambda *_: self.send_g('$X'),
            'disable_motors': lambda *_: self.send_g('$MD'),
            'jog_cancel': lambda *_: self.send_g(b'\x85'),
            'get_status': lambda *_: self.uart('?'),
            'enable_motors': lambda *_: self.send_g('$ME'), 
            'feed_hold': lambda *_: self.send_g(b'!'), # TODO: probably handle this better?
            'send_raw_line': lambda line: self.send_g(line),
            'move.linear': self.move_linear,
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
        self.axes = axes
        self.axes_map = {axis.name: label for label, axis in self.axes.items()} # {axis name: standard}
        print('axis update', self.axes)
        print('axis map', self.axes_map)
        self.gene.register_functions(self, list(self.funcs.keys()), param_is_cnc=True)
        self.update_other()
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    def update_other(self):
        self.iris.webstuff.append(self.webstuff)
       
            
    def __call__(self, state: dict | JSON | bytes, gui=False):
        # example: {'cmd': function, 'data': argument} 
        if isinstance(state, bytes):
            state = state.decode('utf-8')
        if isinstance(state, str):
            state = json.loads(state)
        
        cmd = state.pop('cmd')
        if state != {}:
            self.funcs[cmd](state)
        else:
            self.funcs[cmd]()
                
    async def chk(self):
        while True:
            # do heartbeat, poll grbl
            if utime.ticks_diff(self.next_hbt, utime.ticks_ms()) <= 0:
                self.uart('?')
                self.next_hbt = utime.ticks_add(self.next_hbt, self.hbt_int)

            if self.uart.any():
                msg = self.uart.readline()
                # print(msg)
                if msg == '':
                    continue

                if msg[0] == '<': # grbl info line
                    self.parse_status(msg)

                elif msg == 'ok':
                    print('ok', self.state)
                    if self.state == 'run':
                        print('runnning')
                        self.gene(None)
                    elif self.state == 'mt_buf':
                        self.state = 'idle'
                        print("buffer mt'd")
                        self.gene('secret_key')

                else:
                    print(msg)
                    if self.iris.bifrost is not None:
                        self.iris.bifrost.send(self.pid, {'cmd': 'post', 'data': msg})
            await asyncio.sleep(0)

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


    def move_linear(self, cmd: dict):
        # example: {'cmd': 'move.linear', 'x': 5, 'y': None}
        print(cmd)
        if 'comment' in cmd:
            self.send_bf(cmd.pop('comment'))
        
        if 'feed' in cmd:
            feed = str(cmd.pop('feed'))
        else:
            feed = self.default_feedrate
        feed = f'F{feed}'
        
        # clean empty values
        cmd = {axis: float(val) for axis, val in cmd.items() if val != ''}
        
        # apply offset
        for axis, val in cmd.items():
            cmd[axis] = val + self.offset[axis]
        
        line = ['G1']
        line.extend([f"{k.upper()}{v}" for k,v in cmd.items()])
        line.append(feed)
        
        line = ' '.join(line)
        print(line)
        self.state = 'run'
        self.send_g(line)

    def home(self, axis):
        self.send_g('$H{}'.format(axis.upper()))
        
    def mt_buf(self):
        self.send_g('G04 P.01')
        self.state = 'mt_buf'

    def send_g(self, cmd):
        self.uart(cmd + '\n')
        
    def send_bf(self, msg: str):  # send message to self terminal bifrost
        if self.bifrost is not None:
            self.iris.bifrost.send(self.pid, msg)

    def listdir(self, *args, **kwargs):
        files = os.listdir()
        if 'sd' in files:
            files.extend([f'sd/{file}' for file in os.listdir('sd')])
        files = {'cmd': 'post', 'data': '\n'.join(files)}
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
        status = status_str()
        print(status)
        if self.bifrost:
            msg = {'cmd': 'status'}
            msg.update(self.positions)
            msg['state'] = self.status['state']
            self.send_bf(msg)




