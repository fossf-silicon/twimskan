from floe.iris import Iris
from floe.message import Message
from floe.bifrost import Bifrost

PID = int

class Stater:
    def __init__(self, state: any):
        """ stored constant for use when a remote parameter is not wanted """    
        self.state = state
        self.hot = None
        
    def __call__(self, state) -> None:
        self.state = state
        if self.hot:
                if type(self.hot) is tuple:
                    for h in self.hot:
                        h(self.state)
                else:
                    self.hot(self.state)

    def add_hot(self, hot: callable):
        if self.hot:
            if self.hot is tuple:
                _hot = list(self.hot)
                _hot.append(hot)
                self.hot = tuple(_hot)
            else:
                self.hot = (self.hot, hot)
        else:
            self.hot = hot        
    
class FP:
    '''Future Param, is a holder until all params created then updated with references with update method
    '''
    def __init__(self, pid) -> None:
        self.pid = pid
        
def make_var(item: any) -> Stater | FP:
    """
    Parameter will expect to get value by requesting item.state

    Args:
        item (any | FP): 

    Returns:
        Stater | FP: 
    """
    if isinstance(item, FP):
        return item
    return Stater(item)

