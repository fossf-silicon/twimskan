from floe import FP, make_var
from iris import Iris
import math
from GRBL import GRBL


class GRBLScara(GRBL):
    def __init__(self, *, theta_encoder, phi_encoder, kinematics, name: str, iris: Iris, UART: FP, hbt: int = 1000, x: FP | None, y: FP | None, z: FP | None, a: FP | None, b: FP | None, c: FP | None, webserver_output: bool = False, **k):
        super().__init__(name=name, iris=iris, UART=UART, hbt=hbt, x=x, y=y, z=z, a=a, b=b, c=c, webserver_output=webserver_output, **k)
        self.theta_encoder = make_var(theta_encoder)
        self.phi_encoder = make_var(phi_encoder)
        self.kinematics = make_var(kinematics)
        
        self.prev_cart = None  # this is needed to calculate scara segments
        
        
        #override default functions and make some new
        new_funcs = {
            'home_x': lambda *_: self.run(self._home_theta),
            'home_y': lambda *_: self.run(self._home_phi),
            'reset_x': lambda *_: self.reset('x'),
            'reset_y': lambda *_: self.reset('y'),
            'reset_z': lambda *_: self.reset('z')              
        }
        self.funcs.update(new_funcs)
    
    def update(self):
        self.tool_offsets['default'] = {'p': 0, 'l': 200, 'z': 0}
        self.tool_offsets['camera'] = {'p': -20, 'l': 210, 'z': 10}
        super().update()
        self.change_tool_offset(self.tool_offset)
        
    
    def gui(self):
        return {'name': self.name, 
                'pid': self.pid, 
                'axes': list(self.axes.keys()),
                'axes_map': self.axes_map, 
                'type': 'GRBLScara', 
                'theta_len': self.kinematics.theta_len, 
                'work_offsets': self.work_offsets, 
                'work_offset': self.work_offset,
                'tool_offset': self.tool_offset,
                'tool_offsets': self.tool_offsets,
                }

    def set_tool_offset(self, name: str, vals: dict[str, float]):   
        print('osssss', name, vals)
        self.tool_offsets[name] = vals
        self.kinematics.phi_len = vals['l']
        self.kinematics.phi_2 = vals['l']**2
        self.save()
        self.send_bf({'cmd': 'set_tool_offset', 'data': self.tool_offsets})
        
    def change_tool_offset(self, name:str|dict):
        # name is the key for the work offset
        if isinstance(name, dict): # we got an order
            name = name['data']
        self.tool_offset = name
        phi_len = self.tool_offsets[name]['l']
        self.kinematics.phi_len = phi_len
        self.kinematics.phi_2 = phi_len**2
        self.send_bf({'cmd': 'change_tool_offset', 'data': name})
        
    def get_pos(self, *, kinematics='cartesian'):
        if kinematics == 'cartesian':
            x, y = self.kinematics.fk(self.positions['x'], self.positions['y'] - self.tool_offsets[self.tool_offset]['p'])
            pos = self.positions.copy()
            pos['x'] = round(x, 3)
            pos['y'] = round(y, 3)
            return pos
        else:  # scara
            pos = self.positions.copy()
            pos['t'] = pos.pop('x')
            pos['p'] = pos.pop('y') - self.tool_offsets[self.tool_offset]['p']
            pos['t_encoder'] = self.theta_encoder.state
            pos['p_encoder'] = self.phi_encoder.state
            return pos
        
        # return self.positions
    
    def _home_theta(self):
        """home theta"""
        yield {"cmd": "homing theta"}
        self.reset('x')
        yield {"cmd": "sleep", "seconds": .5}
        yield {"cmd": "homing theta1"}
        # jog grbl to this position with motors disabled
        self.axes['x'].reset(False)
        yield {"cmd": "move", "t": self.theta_encoder.state, "feed": 20000}
        yield {"cmd": "turning motor back on"}
        self.axes['x'].reset(True)
        self.send_g("F500") # reset feed to something reasonable
        yield {"cmd": "Theta Homed"}
    
    def _home_phi(self):
        yield {"cmd": "homing phi"}
        self.reset('y')
        yield {"cmd": "sleep", "seconds": .5}
        # jog grbl to this position with motors disabled
        self.axes['y'].reset(False)
        yield {"cmd": "move", "p": self.phi_encoder.state, "feed": 20000}
        yield {"cmd": "turning motor back on"}
        self.axes['y'].reset(True)
        self.send_g("F500") # reset feed to something reasonable
        yield {"cmd": "Theta Homed"}
        
    def home(self, axis=None):
        if not axis:
            
            self.send_bf('error: no axis specified', post=True)
        elif axis not in self.axes_lookup:
            self.send_bf(f'error: unknown axis: {axis}', post=True)
        elif axis == 't':
            self.run(self._home_theta())
        elif axis == 'p':
            self.run(self._home_phi())
        else:
            """Home the specified axis using GRBL's endstop routine."""
            self.send_g('$H{}'.format(axis.upper()))
    
    def move(self, *, t=None,p=None,x=None,y=None,z=None,a=None,b=None,c=None,f=None):
        order = {'cmd': 'move'}
        axes = {axis: val for axis, val in zip('tpxyzabcf', [t,p,x,y,z,a,b,c,f]) if val is not None}
        if not axes:
            return
        order.update(axes)
        return self._move(order)
    
    def reset(self, axis: str):
        print('resetting', axis)
        _axis = self.axes[axis].reset
        _axis(False)
        _axis(True)
        
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
            self.positions[axis] = self.status['MPos'][axis]
    
        # self.status['limits'] = msg[3]
        # print(status_str())
        if self.bifrost:
            msg = {'cmd': 'status'}
            msg.update(self.positions)
            msg['state'] = self.status['state']
            msg['theta_enc'] = self.theta_encoder.state
            msg['phi_enc'] = self.phi_encoder.state
            self.send_bf(msg)

    def _gline(self, order, rapid=False):
            # example: {'x': 5, 'y': None}
            
            if 'feed' in order:
                feed = str(order.pop('feed'))
            else:
                feed = self.rapid_feedrate if rapid else self.default_feedrate 
            
            feed = f'F{feed}'
            
            # clean empty values
            order = {axis: float(val) for axis, val in order.items() if val != ''}
            
            line = ['G0'] if rapid else ['G1']
            line.extend([f"{k.upper()}{round(v, 3)}" for k,v in order.items()])
            line.append(feed)
            
            line = ' '.join(line)
            print(line)
            self.state = 'run'
            _continue = self.buffer.send(line)
            # if this is called by Gene then we want to return true so we may continue running    
            return _continue

    def _move(self, order: dict):
        print(order)
        wk_off = self.work_offsets[self.work_offset]
        tl_off = self.tool_offsets[self.tool_offset]
            
        valid_codes = ['x', 'y', 'z', 'a', 'b', 'c', 't', 'p', 'f']
        pops = [pop for pop in order if pop not in valid_codes]
        for pop in pops:
            order.pop(pop)
        
        if 'x' in order or 'y' in order:
            # if x or y are in order then we are in cartesian mode
            # calculate scara segments
            if self.prev_cart is None:
                self.prev_cart = self.get_pos(kinematics='cartesian')
            
            if 'x' in order:
                x = order['x']
            else: 
                x = self.prev_cart['x']
            
            if 'y' in order:
                y = order['y']
            else: 
                y = self.prev_cart['y']
            
            point = dict(x=x, y=y)
            self.prev_cart = {'x': point['x'], 'y': point['x']}
            point = self.kinematics.translate(point, work_offset=wk_off)
            point = self.kinematics.ik(point)
            
            order['x'] = point['x']
            order['y'] = point['y'] + tl_off['p']
            
            for axis in ['z', 'a', 'b', 'c']:    
                if axis in order:
                    if order[axis] != "":
                        order[axis] = order[axis]
                        if axis in wk_off:
                            order[axis] -= wk_off[axis]
                        if axis in tl_off:
                            order[axis] += tl_off[axis]
                        if axis == 'a':
                            order[axis] = order[axis] - order['x'] - order['y']
                    else:
                        order.pop(axis) 
            return self._gline(order)
            
        
        elif 't' in order or 'p' in order:
            
            # if t or p are in order then we are in scara mode
            if 't' in order:
                t = order.pop('t')
                if t != "":
                    order['x'] = t
            if 'p' in order:
                p = order.pop('p')
                if p != "":
                    order['y'] = p + tl_off['p']            
            
            for axis in ['z', 'a', 'b', 'c']:    
                if axis in order:
                    if order[axis] != "":
                        order[axis] = order[axis]
                        if axis in wk_off:
                            order[axis] -= wk_off[axis]
                        if axis in tl_off:
                            order[axis] += tl_off[axis]
                    else:
                        order.pop(axis)              
            
            self.prev_cart = None
            return self._gline(order)
        
        else:
            # must be non arm move
            for axis in ['z', 'a', 'b', 'c']:    
                if axis in order:
                    if order[axis] != "":
                        order[axis] = order[axis]
                        if axis in wk_off:
                            order[axis] -= wk_off[axis]
                        if axis in tl_off:
                            order[axis] += tl_off[axis]
                        if axis == 'a':
                            order[axis] = order[axis] - order['x'] - order['y']
                    else:
                        order.pop(axis)
            return self._gline(order)

    