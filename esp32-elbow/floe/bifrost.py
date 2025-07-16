import json
try:
    import uasyncio as asyncio
except:
    import asyncio

class Bifrost:
    """ bifrost is the bridge for the gods. busses and other things are shuffled behind the scenes to the websocket"""
    def __init__(self) -> None:
        self.bifrost = []
        self._checked = [] # to be injected once known to be true
        self.funcs = {}
    
    def send(self, pid: int, msg: str | dict):
        if isinstance(msg, dict):
            msg = json.dumps(msg)

        if self._checked != []:
            self.bifrost.append(f'{pid},{msg}')

        
    def post(self, msg: str):
        self.send('term', msg)

    def any(self) -> bool:
        if self.bifrost != []:
            return True
        return False
    
    def pop(self) -> str: 
        return self.bifrost.pop(0)
        
    # methods below are for cpython, in upython bifrost is handled in server.process_all
    def add_socket(self, manager):
        self.manager = manager
        self._checked = manager.active_connections


    
    async def chk(self):
        while True:
            if self.any():
                await self.manager.broadcast(self.pop())
            await asyncio.sleep(.01)
            # await asyncio.sleep(.02)