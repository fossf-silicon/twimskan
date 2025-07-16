from floe import FP, Iris, make_var
from parameters.GRBL import GRBL



class GRBLScara(GRBL):
    def __init__(self, *, theta_encoder, phi_encoder, name: str, iris: Iris, UART: FP, hbt: int = 1000, x: FP | None, y: FP | None, z: FP | None, a: FP | None, b: FP | None, c: FP | None, webserver_output: bool = False, **k):
        super().__init__(name=name, iris=iris, UART=UART, hbt=hbt, x=x, y=y, z=z, a=a, b=b, c=c, webserver_output=webserver_output, **k)
        self.theta_encoder = make_var(theta_encoder)
        self.phi_encoder = make_var(phi_encoder)
        
        self.prev_cart = None  # this is needed to calculate scara segments
        
        #override default functions and make some new
        new_funcs = {
            'home_x': lambda *_: self.run(self.home_theta),
            'home_y': lambda *_: self.run(self.home_phi),
            'reset_x': lambda *_: self.reset('x'),
            'reset_y': lambda *_: self.reset('y'),
            'reset_z': lambda *_: self.reset('z')              
        }
        self.funcs.update(new_funcs)
           
        
        self.webstuff = {'name': name, 'pid': self.pid, 'type': 'GRBLScara'}
    
    
    def update_other(self):
        print(self.webstuff)
        self.iris.webstuff.append(self.webstuff)
    
    def home_theta(self):
        yield {"cmd": "homing theta"}
        self.reset('x')
        yield {"cmd": "sleep", "seconds": .5}
        yield {"cmd": "homing theta1"}
        # jog grbl to this position with motors disabled
        self.axes['x'].reset.pin.value(False)
        yield {"cmd": "move.linear", "x": self.theta_encoder.state, "feed": 20000}
        yield {"cmd": "turning motor back on"}
        self.axes['x'].reset.pin.value(True)
        self.send_g("F500") # reset feed to something reasonable
        yield {"cmd": "Theta Homed"}
    
    def home_phi(self):
        yield {"cmd": "homing phi"}
        self.reset('y')
        yield {"cmd": "sleep", "seconds": .5}
        # jog grbl to this position with motors disabled
        self.axes['y'].reset.pin.value(False)
        yield {"cmd": "move.linear", "y": self.phi_encoder.state, "feed": 20000}
        yield {"cmd": "turning motor back on"}
        self.axes['y'].reset.pin.value(True)
        self.send_g("F500") # reset feed to something reasonable
        yield {"cmd": "Theta Homed"}
        
        
    def reset(self, axis: str):
        print('resetting', axis)
        _axis = self.axes[axis].reset
        state = _axis.state
        _axis.pin.value(not state)
        _axis.pin.value(state)
        

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
            msg['theta_enc'] = self.theta_encoder.state
            msg['phi_enc'] = self.phi_encoder.state
            self.send_bf(msg)



