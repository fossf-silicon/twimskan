from parameters.Parameter import Parameter

class CPythonCore(Parameter):
    """this is mostly to make the ide work well
    it will hold stuff and then deliver them nicely to iris on update()"""
    def __init__(self, *, name: str = "", bus: int, terminal: int, **k):
        super().__init__(**k)
        self.name = name
        self.bus = bus
        self.terminal = terminal
        