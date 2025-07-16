"""
Neopixel Rainbow Animation
"""
import math

class Rainbow:
    """ rainbow animation for Neo
    """
    rbow = tuple([int((math.sin(math.pi / 18 * i) * 127 + 128) / 10) for i in range(36)])
    
    def __init__(self, *, pid, iris, **k):
        self.pid = int(pid)
        self.index = 0
    
        iris.p[pid] = self
        
    def __call__(self, *args, **kwargs):
        pass
    
    def animate(self, neo):
        for i in range(neo.num_pix):
            neo.neo[i] = (self.rbow[self.index], self.rbow[(self.index + 12)%36], self.rbow[(self.index + 24)%36])
        neo.neo.write()
        self.index = (self.index + 1) % 36
       
    def update(self):
        pass
