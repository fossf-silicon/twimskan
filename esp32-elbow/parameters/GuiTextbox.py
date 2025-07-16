from parameters.Parameter import Parameter
import floe.bifrost

class GuiTextbox(Parameter):
    struct = 'u'  # utf8
    
    def __init__(self, *, name: str = "", initial_value=False, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.state = initial_value
        
        element = {"name": name, "pid": self.pid, "initial_value":initial_value, "type": "text_input"}
        
        self.iris.webstuff.append(element)
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        # super().__call__()
        self.state = state
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
        if self.hot:
            if type(self.hot) is tuple:
                for h in self.hot:
                    h(self.state)  # h = Parameter
            else:
                self.hot(self.state)

