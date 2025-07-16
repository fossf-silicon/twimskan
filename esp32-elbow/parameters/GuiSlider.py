from parameters.Parameter import Parameter
import floe.bifrost

class GuiSlider(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, *, name: str = "", min: int=0, max: int=100, initial_value=0, output_float, invert, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.max = max
        self.min= min
        self.state = initial_value
        self.output_float = output_float
        self.invert = invert
        
        # create the web element and hand it off to iris for her to create webpage
        element = {"name": name, "pid": self.pid, "min": min, "max": max, "initial_value": initial_value, "type": "slider"}
        self.iris.webstuff.append(element)
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            state = int(state.decode('utf8'))
        super().__call__(state)
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
       
