"""
Digital Output for ESP32
"""
from floe import FP, make_var
from parameters.Parameter import Parameter

try:
    from machine import Pin
except:
    from fakes.machine import Pin


class DigitalOutput(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, pin: int, invert: bool | FP, initial_value: bool, **k):
        super().__init__(**k)
        self.invert = make_var(invert)
        self.state = initial_value
        self.pin = int(pin)

        # self.iris.hw_outs.append(self)

    def __call__(self, state) -> None:
        super().__call__(state)
        self.hw()

    def update(self):
        super().update()
        self.pin = Pin(int(self.pin), mode=Pin.OUT)
        
        if self.invert.state:
            self.pin.value(not self.state)
        else:
            self.pin.value(self.state)

    def hw(self):
        if self.invert.state:
            # print(f"writing pin: to {not self.state}")
            self.pin.value(not self.state)
        else:
            # print(f"writing pin: to {not self.state}")
            self.pin.value(self.state)