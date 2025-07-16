from parameters.Parameter import Parameter, ACTIVE, DBG_SRL, HOT


class If(Parameter):
    """Note: Truths may only speak to parameters on *this* board"""
    struct = '?'  # bool

    def __init__(self, if_true: list[int], _else: list[int], invert=False, initial_state=False, **k):
        self.invert = invert
        self.state = initial_state
        self.if_true = if_true
        self._else = _else
        
    def update(self):
        self.if_true = [self.iris.p[pid] for pid in self.if_true]
        self._else = [self.iris.p[pid] for pid in self._else]
    
    def __call__(self, state):
        if state is None:
            self.send()
            return

        self.state = state
        self.send()
    
    def add_hot(self):
        pass

    def send(self) -> None:
        if self.blob & ACTIVE:  # ACTIVE
            if self.state:
                if not self.invert:
                    for pid in self.if_true:
                        pid(None)
                else:
                    for pid in self._else:
                        pid(None)
            else:
                if not self.invert:
                    for pid in self._else:
                        pid(None)
                else:
                    for pid in self.if_true:
                        pid(None)

        
            if self.blob & DBG_SRL:  # DEBUG SERIAL
                print(f'DEBUG: pid: {self.pid}, state: {self.state}')
            