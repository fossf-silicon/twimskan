from parameters.Parameter import Parameter
import floe.bifrost

class GuiButton(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, name: str = "", **k):
        super().__init__(name=name, **k)
        self.name = name
        
        element = {"name": name, "pid": self.pid, "color": "green", "type": "button"}
        self.iris.webstuff.append(element)
    
    def __call__(self, state, gui=False):
        # super().__call__()
        self.state = state
        # print(self.name, self.state)
        if not gui:
            floe.bifrost.send({'cmd': 'evt', 'msg': [self.pid, self.state]})
        if self.hot:
            if type(self.hot) is tuple:
                for h in self.hot:
                    h(self.state)  # h = Parameter
            else:
                self.hot(self.state)
