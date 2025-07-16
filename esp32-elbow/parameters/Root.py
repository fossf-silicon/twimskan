from parameters.Operator import Operator

class Root(Operator):
    def __init__(self, input1=0, input2=0, **k):
        super().__init__(input1, input2, **k)
    
    def code(self):
        return self.input1.state ** (1/self.input2.state)