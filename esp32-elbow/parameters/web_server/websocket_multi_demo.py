from ws_connection import ClientClosedError
from ws_server import WebSocketClient
from ws_multiserver import WebSocketMultiServer


class TestClient(WebSocketClient):
    def __init__(self, conn):
        super().__init__(conn)

    def process(self):
        try:
            msg = self.connection.read()
            if not msg:
                return
            msg = msg.decode("utf-8")
            print(msg)
            self.connection.write(f"echo: {msg}")
#             items = msg.split(" ")
#             cmd = items[0]
#             if cmd == "Hello":
#                 self.connection.write(cmd + " World")
#                 print("Hello World")
        except ClientClosedError:
            self.connection.close()


class TestServer(WebSocketMultiServer):
    def __init__(self, home, conns, pages):
        super().__init__(home, conns, pages)

    def _make_client(self, conn):
        return TestClient(conn)

pages = {"/": "test.html", "/about": "about.html"}
server = TestServer("static/test.html", 10, pages)
server.start()
try:
    while True:
        server.process_all()
except KeyboardInterrupt:
    pass
server.stop()
