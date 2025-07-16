from parameters.web_server.ws_connection import ClientClosedError
from parameters.web_server.ws_server import WebSocketClient
from parameters.web_server.ws_multiserver import WebSocketMultiServer
import uasyncio as asyncio
import json
from floe import Iris
from parameters.web_server.repl import do_repl




class Client(WebSocketClient):
    def __init__(self, conn, iris):
        super().__init__(conn)
        self.iris = iris
        
    def process(self):
        try:
            msg = self.connection.read()
            if not msg:  # we will send messages out when there are no new messages in
                if self.iris.bifrost.any():
                    line = self.iris.bifrost.pop()
                    self.connection.write(line)
                return
            print(msg)
            if msg == b'get_webstuff':
                self.connection.write(f'compose_page,{json.dumps(self.iris.webstuff)}')
            
            ##PID##,$$DATA$$ <- message format
            comma = msg.find(b',')
            if comma == -1:
                return f'unknwn thing from socket {msg}'
            pid = msg[:comma]
            data = msg[comma+1:]
            
            if not msg:
                return
            
            if pid == b'term':
                code = data.decode("utf-8")
                self.connection.write(f'term,{do_repl(code, self.iris)}')
                return
            
            pid = int(pid.decode("utf-8"))
            if data == b'true':
                data = True
            if data == b'false':
                data = False
            
            try:
                print('processing', pid, data)
                self.iris.p[pid](data, gui=True)
            except Exception as e:
                print('exception', e)

        except ClientClosedError:
            self.connection.close()
   

class WebServer(WebSocketMultiServer):
    def __init__(self, *,
                 iris: Iris,
                 homepage: str = "static/terminal.html", 
                 simultanious_conns: int = 1, 
                 pages: dict[str, str]= {"/": "terminal.html", "/about": "about.html"}, 
                 ):
        super().__init__(homepage, simultanious_conns, pages)
        
        # print('clients!!!', self._clients)
        
        self.iris = iris
        self.iris.bifrost._checked = self._clients
        iris.p[-1] = self
        self.start()
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk()) 
                    
    async def chk(self):
        while True:
            self.process_all()
            await asyncio.sleep_ms(0)

    def _make_client(self, conn):
        return Client(conn, self.iris)




        


