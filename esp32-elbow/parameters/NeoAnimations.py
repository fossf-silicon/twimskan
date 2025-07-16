"""
Initial implemetation of NeoPixel Animations
"""

from floe import FP, make_var
from parameters.Parameter import Parameter
try:
    import uasyncio as asyncio
except:
    import asyncio




class NeoAnimations(Parameter):
    struct = 'h'  # int16
    
    def __init__(self, *, neo: FP, animations: list[FP], delay: int, initial_value: int=0, **k):
        super().__init__(**k)
        self.neo = neo
        self.animations = animations
        self.iris.h.append(self)
        self.delay = make_var(delay)
        self.state = initial_value
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
        
    def __call__(self, state, **k) -> None:
        if state is None:
            super().send()
            return
        self.state = state
        if self.state == 0:
            self.neo(b'\x00\x00\x00')  # turn off the pixels
        
        
    def update(self):
        super().update()
        if not isinstance(self.animations, list):
            self.animations = [self.animations]
        self.animations = [self.iris.p[animation.pid] for animation in self.animations]
        
            
    
    async def chk(self):
        while True:
            if self.state != 0:
                self.animations[self.state - 1].animate(self.neo)
            await asyncio.sleep_ms(self.delay.state)
                
    