"""
Neopixel Parameter for ESP32
"""

from parameters.Parameter import Parameter
try:
    import machine
except:
    import fakes.machine as machine
try:
    from neopixel import NeoPixel as NP
except:
    from fakes.neopixel import NeoPixel as NP
    
    
class NeoPixel(Parameter):
    struct = 'e'  # bytearray[3]
    
    def __init__(self, number_of_pixels, pin, **k):
        super().__init__(**k)
        self.num_pix = int(number_of_pixels)
        self.neo = NP(machine.Pin(pin, machine.Pin.OUT), number_of_pixels)
        self.fill(b'\x00\x00\x00')

    def __call__(self, state: bytearray):
        if state is not None:
            self.state = state
        self.fill(state)
        super().__call__(state)
        
    def fill(self, color: bytearray):
        for pix in range(self.num_pix):  # fill the strip/ring
            self.neo[pix] = (color[0], color[1], color[2])
            self.neo.write()
