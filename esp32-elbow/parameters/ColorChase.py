
from floe import make_var

class ColorChase:
    """ color animation for Neo
    """
    RGB = bytearray
    struct = 'e'  # buffer
    
    def __init__(self, pid, dot_color: bytearray, fill_color: bytearray, iris, **k) -> None:
        self.pid = pid
        # this is a hack until color picker is implimented
        if dot_color is None:
            dot_color = b'\x00\x09\x03'
        if fill_color is None:
            fill_color = b'\x00\x02\x03'
        
        self.index = 0
        self.dot_color = make_var(dot_color)
        self.fill_color = make_var(fill_color)
        
        iris.p[pid] = self       

    def animate(self, neo):
        self.index += 1
        self.index %= neo.num_pix
        for pixel in range(neo.num_pix):
            if self.index == pixel:
                neo.neo[pixel] = self.dot_color.state
            else:
                neo.neo[pixel] = self.fill_color.state
        neo.neo.write()
    
    def update(self):
        pass
