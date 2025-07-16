from parameters.Operator import Operator

class LessThan(Operator):
    def __init__(self, input1=0, input2=0, **k):
        super().__init__(input1, input2, **k)
    
    def code(self):
        return self.input1.state < self.input2.state