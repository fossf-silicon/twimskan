"""
ESP32 pwm driver    
"""
from floe import FP, make_var, Stater
from parameters.Parameter import Parameter
try:
    import machine
except:
    import fakes.machine as machine
try:
    import utime
except:
    import fakes.utime as utime

class PWM(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, pin, freq, duty, duty_min: float, duty_max: float, invert_duty, **k):
        super().__init__(**k)
        self.pin = pin
        self.freq = make_var(freq)
        self.duty = make_var(duty)
        self.duty_min = make_var(duty_min)
        self.duty_max = make_var(duty_max)
        self.invert_duty = make_var(invert_duty)

        
    def __call__(self, state: bool, **k):
        super().__call__(state)
        if state is not None:
            if self.state != state:
                self.hw(state)
        

    def update(self):
        super().update()
        # Set up hardware
        self.pin = machine.PWM(machine.Pin(self.pin), freq=self.freq.state)
        utime.sleep_ms(1)
        self.set_duty(self.duty.state)
        # self.iris.hw_outs.append(self.pid)
        
        self.duty.add_hot(self.set_duty)
        self.freq.add_hot(self.pin.freq)
        
    def set_duty(self, state: float):
        if self.invert_duty.state:
            state = -(state - 1)
        dif = self.duty_max.state - self.duty_min.state
        duty = state * dif
        duty += self.duty_min.state

        duty = int(duty*1024)
        self.pin.duty(duty)
                
    def hw(self, state):
        if state:
            print(f'init pwm with freq: {self.freq.state}, duty: {self.duty.state}')
        else:
            print('de init pwm')
