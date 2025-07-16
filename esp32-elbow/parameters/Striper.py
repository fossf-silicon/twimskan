from parameters.Parameter import Parameter

class Striper(Parameter):
    """
    Striped object for large data transmission
    """

    def __init__(self, head: int, stripe: list[int], **k):
        super().__init__(**k)
        self.head = head  # base pid, send message here to end buffer short
        self.stripe = stripe  # list of pids, *note pids exist only in iris.s as subscriptions

    def __call__(self, buf):
        if not self.blob:
            return
        if type(buf) is str:
            buf = buf.encode()
        for pid in self.stripe:
            if not buf:
                break
            if len(buf) >= 8:
                seg = buf[:8]
                buf = buf[8:]
                self.iris.send(pid=pid, w=False, load=seg)
            else:
                self.iris.send(pid=pid, w=False, load=buf)
                break