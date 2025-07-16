"""
Analog Input for ESP32
"""

from floe import FP, make_var
from parameters.Parameter import Parameter
try:
    import machine
except:
    import fakes.machine as machine
try:
    import uasyncio as asyncio
except:
    import asyncio    

class AnalogInput(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, pin, delay, ring_size, noise_reduction, low=0, high=65535, **k):
        super().__init__(**k)
        self.low = low      # not implemented yet
        self.high = high    # not implemented yet
        self.delay = delay
        self.dif = noise_reduction
        self.ring_size = ring_size
        # Set up hardware
        self.pin = machine.ADC(machine.Pin(pin))
        initial_val = self.pin.read_u16()
        self.ring = [initial_val] * ring_size
        self.state = initial_val
        self.index = 0
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())

        
    async def chk(self):
        while True:
            self.ring[self.index] = self.pin.read_u16()
            self.index += 1
            if self.index == self.ring_size:
                self.index = 0
            state = sum(self.ring)//self.ring_size
            if abs(self.state - state) > self.dif:
                self.state = state
                self.send()
            await asyncio.sleep_ms(self.delay)