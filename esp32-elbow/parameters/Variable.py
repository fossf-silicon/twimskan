from parameters.Parameter import Iris, Parameter, FP, PID

class Variable(Parameter):
    def __init__(self, *, datatype: str, iris: Iris, state: any = None, pid: int = 0, **k):
        super().__init__(pid=pid, iris=iris, state=state, **k)
        self.struct = self.datatypes[datatype]

        




            