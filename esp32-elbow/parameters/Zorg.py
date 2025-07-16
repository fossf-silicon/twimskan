


class Zorg:
    def __init__(self, *, pid, iris, **k) -> None:
        
        self.pid = pid
        
        iris.p[self.pid] = self
        
    def update(self):
        pass