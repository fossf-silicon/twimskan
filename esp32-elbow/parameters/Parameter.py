from floe import Iris, FP, PID


# blob constants
ACTIVE = 1
SND2OB = 2
SND2IIB = 4
DBG_SRL = 8
HOT = 16
PARTIAL = 32
ALIAS = 64
LOGGING = 128




class Parameter:  # Abstract class
    datatypes = {
        'bool': '?',
        'byte': 'b',
        'unbyte': 'B',
        'sint16': 'h',
        'int16': 'H',
        'int32': 'i',
        'unint': 'I',
        'int64': 'q',
        'unint64': 'Q',
        'float32': 'f',
        'double': 'd',
        'buf': 'e',
        'utf8': 'u'
    }
    
    
    # __slots__ = ('pid', 'state', 'struct', 'p', 'iris', 'blob', 'hot')
    def __init__(self, *, pid: int=0, iris: Iris, state: any = None, name=None, active=False, debug=False, bcast=False, **k):
        self.pid = int(pid)
        self.state = state

        self.p = iris.p
        self.iris = iris

        # blob package: [hot, debug, broadcast(self), broadcast(bus), active] >>>LSB
        self.blob = 0
        if active:
            self.blob |= ACTIVE
        if debug:
            self.blob |= DBG_SRL
        if bcast:
            self.blob |= SND2OB

        self.hot = None
        self.partial = None
        self.alias = None
        iris.p[self.pid] = self
        if iris.zorg:
            iris.locals[name] = self

    # ------------------------------------------------------------------------

    def __call__(self, state) -> None:
        if state is not None:
            self.state = state
        # print(f'current state is {self.state}')
        self.send()

    def update(self):
        for attr, val in self.__dict__.items():            
            if isinstance(val, FP):
                setattr(self, attr, self.iris.p[val.pid])

    
    def add_hot(self, hot: any):  # int | str | callable
        self.blob |= HOT
        if isinstance(hot, str):
            hot = self.p[int(hot)]
        elif isinstance(hot, int):
            hot = self.p[hot]
        
        if self.hot:
            if self.hot is tuple:
                _hot = list(self.hot)
                _hot.append(hot)
                self.hot = tuple(_hot)
            else:
                self.hot = (self.hot, hot)
        else:
            self.hot = hot
  
    # def add_partial(self, partial: tuple[int, any]):
    #     partial = (self.p[partial[0]], partial[1])
        
    #     if self.partial:
    #         if self.partial is tuple:
    #             part = list(self.partial)
    #             part.append(partial)
    #             self.partial = tuple(part)
    #         else:
    #             self.partial = (self.partial, partial)
    #     else:
    #         self.partial = partial
            
    # ------------------------------------------------------------------------

    def send(self, cmd=0, pid=None, adr=None) -> None:
        if self.blob & ACTIVE:  # ACTIVE
            if self.blob & SND2OB:  # SEND TO OUTBOX
                if pid is None:
                    pid = self.pid
                self.iris.send(pid=pid,
                               load=self.iris.msg.bundle(self.state, self.struct),
                               type=cmd,
                               adr=adr)
            # if self.blob & SND2IIB:  # YIELD
            #     self.iris.send_i((self.pid, self.state))
            if self.blob & DBG_SRL:  # DEBUG SERIAL
                print(f'DEBUG: pid: {self.pid}, state: {self.state}')

            if self.blob & HOT:  # CALL param with self
                if isinstance(self.hot, tuple):
                    for h in self.hot:
                        h(self.state)  # h = Parameter
                else:
                    self.hot(self.state)

            # if self.blob & PARTIAL:  # PARTIAL call param with constant
            #     if type(self.partial[0]) is tuple:
            #         for f in self.partial:
            #             f[0](f[1])  # f = (Parameter, any)
            #     else:
            #         self.partial[0](self.partial[1])

            # if self.blob & ALIAS:  # ALIAS call param with foreign p.state
            #     if type(self.alias[0]) is tuple:
            #         for a in self.partial:
            #             a[0](a[1].state)  # a = (Parameter, Parameter)
            #     else:
            #         self.alias[0](self.alias[1].state)

            # if self.blob & LOGGING:
            #     print(f'MAKE LOGGER: pid: {self.pid}, state: {self.state}')
