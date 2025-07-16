import struct
from collections import namedtuple
'''
potential message packing
[data][header][len]
'''

Functor = namedtuple('Functor', ('pid', 'arg'))


class Message:
    def __init__(self, iris):
        self.s = iris.s  # subscription list
        self.p = iris.p  # p
        self.send = iris.send
        self.iris = iris
        self.uuid = None
        # single items, len(bytearray) >= 8

        self.encodings = ('utf8', 'ascii')

    # ------------------------------------------------------------------------
    """
    Types:
        4: INFO         : push info back to caller for things like deprication warnings etc.
        3: RPC Reply    : RPC Reply
        2: RPC Call     : RPC Call    [commands and queries]
        1: write        : crud
        0: None         : generic broadcast
        
        can     [parameter priority bits][address bits][parameter bits][type]
        mqtt    [address]/[parameter id]/[type]
        rabbit  [address].[parameter id].[type]
        kafka   [address].[parameter id].[type]
    """

    def want(self, msg_adr, pid, type, h, self_adr):
        if msg_adr == 0:                                    # FAULT
            return self.do_flt, pid
        elif msg_adr == 1:                                  # NWK
            return self.do_nwk, pid
        elif msg_adr == 2:                                  # ZORG
            return self.do_zorg, pid
        elif msg_adr == self_adr:
            print('message for self')
            if type == 1:                                   # WRITE
                if pid in self.p:
                    return self.do_write, pid
                print('no param here')
            elif type == 2:                                 # QUERY
                return self.do_query, pid
        elif h in self.s:
            if type == 0:                                   # BROADCAST - default
                return self.do_sub, self.s[h]
            elif type == 3:                                 # QUERY REPLY
                return self.do_query_reply, self.s[h]
            elif type == 4:                                 # INFO (from reply)
                return self.do_info, self.s[h]

        return False, None


    def do_flt(self, load: bytearray, h: int) -> None:
        """ process fault message """
        print(f'We are dangerous here, got fault {h}: {load}')

    def do_nwk(self, load: bytearray, h: int) -> None:
        """ process nwk message"""

        # TODO: finalize fault bits for now it's 10
         # offset for faults
        # print('network message', h)
        if h < 2048: # these are adr assignment messages
            if load == self.uuid:
                self.iris.header.adr = h - 1024
        elif -h in self.p:
            self.p[-h](self.unbundle(load=load, type=self.p[-h].struct))
        # print(f'seeking {-h}')
        # if nwk_h in nwk_functions:
        #     nwk_functions[nwk_h](load)
        #

    def do_zorg(self, load: bytearray, h: int):
        pass

    def do_write(self, load: bytearray, pid) -> None:
            if pid < 500:  # TODO: find place for self functions
                self.p[pid](load)
            else:
                self.p[pid](self.unbundle(load=load, type=self.p[pid].struct))


    def do_query(self, load: bytearray, h: int):
        print('figure out how to handle queries')
    
    def do_sub(self, load: bytearray, sub: list[str|int, str]):
        # print('sub', h)
        data = self.unbundle(type=sub[1], load=load)
        # print('parsing', sub, data)

        # subscription contains extra arguments
        # sub: (pid, struct)
        # sub: (pid, struct, args)
        # sub: ((pid, pid), struct)
        # sub: ((pid, pid), struct, args)

        if type(sub[0]) is not tuple:  # single sub
            if len(sub) > 2:
                self.p[sub[0]](data, *sub)

            else:  # regular subscription
                self.p[sub[0]](data)
            return

        for s in sub[0]:  # multiple sub
            if len(sub) > 2:
                self.p[s](data, s, *sub[1:])
            # regular subscription
            else:
                self.p[s](data)

    def do_query_reply(self, load: bytearray, h: int):
        pass
    
    def do_info(self, load: bytearray, h: int):
        pass
        
    # ------------------------------------------------------------------------

    @staticmethod
    def unbundle(load: bytearray, type: str) -> any:
        bundles = {
            'b': lambda l: struct.unpack('b', l)[0],        # signed char
            'B': lambda l: struct.unpack('B', l)[0],        # unsigned char
            '?': lambda l: bool(struct.unpack('b', l)[0]),  # bool
            'h': lambda l: struct.unpack('h', l)[0],        # short int16
            'H': lambda l: struct.unpack('H', l)[0],        # unsigned short unint16
            'i': lambda l: struct.unpack('i', l)[0],        # int
            'I': lambda l: struct.unpack('I', l)[0],        # unsigned int
            'q': lambda l: struct.unpack('q', l)[0],        # long
            'Q': lambda l: struct.unpack('Q', l)[0],        # unsigned long
            'f': lambda l: struct.unpack('f', l)[0],        # float
            'd': lambda l: struct.unpack('d', l)[0],        # double
            'e': lambda l: l,                               # return the buffer
            'a': lambda l: l.decode('ascii'),               # decode as ascii
            'u': lambda l: l.decode('utf8')                 # decode as utf8
        }
        # micropython has no defaultdict
        try:
            return bundles[type](load)
        except KeyError:
            # must be collection
            print(f'unknown type, trying to unpack with {type} as type')
            return struct.unpack(type, load)

    # ------------------------------------------------------------------------

    @staticmethod
    def bundle(load: any, type: str) -> bytes:
        bundles = {
            'b': lambda l: struct.pack('b', l),  # signed char
            'B': lambda l: struct.pack('B', l),  # unsigned char
            '?': lambda l: struct.pack('b', l),  # bool
            'h': lambda l: struct.pack('h', l),  # short
            'H': lambda l: struct.pack('H', l),  # unsigned short
            'i': lambda l: struct.pack('i', l),  # int
            'I': lambda l: struct.pack('I', l),  # unsigned int
            'q': lambda l: struct.pack('q', l),  # long
            'Q': lambda l: struct.pack('Q', l),  # unsigned long
            'f': lambda l: struct.pack('f', l),  # float
            'd': lambda l: struct.pack('d', l),  # double
            'e': lambda l: l,                    # return the buffer
            'a': lambda l: l.encode(),           # encode string
            'u': lambda l: l.encode()            # encode string
        }

        try:
            return bundles[type](load)
        except KeyError:
            # must be collection
            # TODO: handle collections with non struct items
            return struct.pack(type, *load)

