from parameters.Parameter import Parameter, SND2IIB, DBG_SRL, HOT


class Stripe(Parameter):
    """
    Striped buffer for large data transmission, receives from striper
    """

    def __init__(self, encode=None, *, len: int, **k):
        super().__init__(**k)
        self.buf = [b''] * len
        self.encode = encode

    def __call__(self, num_blocks, *args):
        """
        if this parameter is written to directly it can close buffer before it is full
        *args will be included if sub pid is called
        (pid, struct, block_index)
        """
        if args:  # written to through stripe pid
            print(args)
            self.buf[args[2]] = num_blocks  # in this case num_blocks is a bytearray from the bus
            if b'' not in self.buf:  # message complete
                print(self.buf)
                self.send(self.buf)
                return
            print(self.buf)
            return

        # are all blocks in stripe written to?
        if b'' not in self.buf[:num_blocks]:
            self.send(self.buf[:num_blocks])
        else:
            print('error create nak routine')
            raise ValueError

    def send(self, buf):
        ret = b''.join(buf)
        print(ret)
        self.buf = [b'' for _ in self.buf]
        if self.blob:
            if self.blob & SND2IIB:  # SEND TO IIB
                if self.encode:
                    self.iris.send_i((self.pid, ret.decode(self.encode)))
                else:
                    self.iris.send_i((self.pid, ret))
            if self.blob & DBG_SRL:  # DEBUG SERIAL
                print(f'DEBUG: pid: {self.pid}, state: {ret}')
            if self.blob & HOT:  # SEND HOT
                if type(self.hot) is tuple:
                    for h in self.hot:
                        self.p[h](ret)
                else:
                    self.p[self.hot](ret)