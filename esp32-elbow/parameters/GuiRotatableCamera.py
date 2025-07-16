from parameters.Parameter import Parameter
import floe.bifrost

class GuiRotatableCamera(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, *, name: str = "", url, **k):
        super().__init__(name=name, **k)
        self.name = name
        
        # create the web element and hand it off to iris for her to create webpage
        element = {"name": name, "pid": self.pid, "url": url, "type": "GuiRotatableCamera"}
        self.iris.webstuff.append(element)
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            state = int(state.decode('utf8'))
        super().__call__(state)
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
       
