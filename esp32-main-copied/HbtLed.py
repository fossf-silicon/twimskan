"""
Heartbeat Led for ESP32  
"""

from Parameter import Parameter
try:
    from machine import Pin
except:
    from fakes.machine import Pin
try:
    import uasyncio as asyncio
except:
    import asyncio
    
    
class HbtLed(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, pin: int, delay: int, **k):
        super().__init__(**k)
        self.pin = Pin(int(pin), mode=Pin.OUT)
        self.delay = int(delay)
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    async def chk(self):
        while True:
            self.pin.value(not self.pin.value())
            await asyncio.sleep_ms(self.delay)
            
    