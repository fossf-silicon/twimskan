from parameters.Parameter import Parameter, DBG_SRL, HOT

class Switch(Parameter):
    """Note: Switches may only speak to parameters on self"""

    def __init__(self, items: list[any], **k):
        super().__init__(**k)
        self.items = tuple(
            [tuple([tuple(i) for i in item]) if type(item[0]) is list else tuple(item) for item in items])

    def __call__(self, index):
        if index is None:
            self.send()
            return

        self.state = index
        self.send()

    def send(self):
        if self.state is None:
            return
        switch = self.items[self.state]
        if self.blob:
            if self.blob & DBG_SRL:  # DEBUG SERIAL
                print(f'DEBUG: pid: {self.pid}, hot-route: {switch}')
            if self.blob & HOT:  # SEND HOT
                if type(switch[0]) is tuple:
                    for h in switch:
                        self.p[h[0]](h[1])
                else:
                    self.p[switch[0]](switch[1])
