from parameters.Parameter import Parameter
from floe import make_var

class Operator(Parameter):
    """Operator is the parent class for things like math, logic and boolean operators"""
    def __init__(self, input1, input2, **k):
        super().__init__(**k)
        self.input1 = make_var(input1)
        self.input2 = make_var(input2)
        self.state = 0

    def __call__(self, state):
        '''state is ignored and whole expression is evaluated'''
        self.state = self.code()
        super().__call__(self.state)
        
    def update(self):
        super().update()
        self.state = self.code()
        self.input1.add_hot(self)
        self.input2.add_hot(self)
        
    def code(self):
        '''this should be overridden by child classes'''
        return None