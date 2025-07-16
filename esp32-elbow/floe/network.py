import json

print('importing network')
import os
import floe.parameters as parameters
from floe.iris import iris
send = iris.send
import hashlib
try:
    import machine
except:
    from fakes import machine

class PFunc:
    """
    simple class with just enough that message will unbundle payload on receive
    """
    def __init__(self, struct, func):
        self.struct = struct
        self.func = func

    def __call__(self, msg):
        self.func(msg)

class SendFile:
    def __init__(self, struct):
        self.struct = struct

    def __call__(self, msg, filename, pid, file2send):
        ''' msg should be the adr of the requestor'''
        gen = parameters.create_file_sender(filename=filename, file2send=file2send, packet_size=50)
        send(pid=pid, type=1, load=gen, adr=msg, gen=True)

def get_hash(filename: str) -> bytes:
    hasher = hashlib.sha256()
    with open(filename, 'rb') as f:
        hasher.update(f.read())
    return hasher.digest()[:8]


def send_mani(msg, pid, filename, file2send):
    print('sending mani')
    gen = parameters.create_file_sender(filename=filename, file2send=file2send, packet_size=iris.bus.header.packet_size)
    send(pid=pid, type=1, load=gen, adr=msg, gen=True)



def compare_mani_hash(msg):
    print('comparing manifests')
    my_hash = get_hash('manifest.json')
    if msg != my_hash:
        print(f'{msg}: {my_hash}, send message to request updated manifest')


def compare_map_hash(msg):
    print('comparing maps')
    my_hash = get_hash('map.json')
    if msg != my_hash:
        print(f'{msg}: {my_hash}, send message to request updated map')

def compare_network_hash(msg):
    print('comparing network.py')
    my_hash = get_hash('floe/network.py')
    if msg != my_hash:
        print(f'{msg}: {my_hash}, send message to request updated network.py')

def ping(msg):
    print('pinging it')
    send(pid=1024, type=1, load='this is uuid', adr=0)  # 0/

def file_struct(msg):
    files = []

    def parse_dir(dir: list[str], current_dir=''):
        for file in dir:
            if file.find('.') != -1:
                files.append(f'{current_dir}{file}')
            else:
                if file != 'venv':
                    next_dir = f'{current_dir}{file}/'
                    print(next_dir)
                    parse_dir(os.listdir(next_dir), next_dir)

    parse_dir(os.listdir())
    iris.p[-2051](json.dumps(files))

nwk_functions = {
    -2048: PFunc('e', ping),            # pub('0/2048', b'{')
    -2049: None,                        # ping response from -2048
    -2050: PFunc('e', file_struct),     # pub('0/2050', b'{')
    -2051: parameters.Stringer(2051, iris=iris, blob=9),  # response to file struct request
    -4105: parameters.FileReceiver(pid=-2052, iris=iris, blob=9, state=False, d_type=['buf', 'e']),
    -4106: PFunc('e', lambda m: machine.reset()) 
}


zorg_functions = {
    -10000: PFunc('B', lambda m: send_mani(m, 2052, 'subscriptions.json', 'subscriptions.json')),
    # 6144                        # 6144
    -10001: PFunc('e', lambda m: print('req map message')),  # 6146
    -10002: PFunc('e', lambda m: print('request mani hash')),  # 6148
    -10003: parameters.StrBuf(pid=10003, iris=iris, blob=25, d_type=['buf', 'e']),
    -10005: lambda m, f: print(m,f), # hot route from -10003
    -10010: PFunc('B', lambda fname: send_mani(0, 2052, fname, fname)),
}

base_parameters = {
    700: parameters.FileReceiver(pid=349, iris=iris, blob=9, state=False, d_type=['buf', 'e']),
    701: PFunc('e', compare_mani_hash),
    702: PFunc('e', compare_map_hash),
    703: PFunc('e', compare_mani_hash), # this is this file
}
for k, v in base_parameters.items():
    iris.p[k] = v
for k, v in nwk_functions.items():
    iris.p[k] = v

def make_me_zorg():
    print('zorging zorg will now zorg')
    for k, v in zorg_functions.items():
        iris.p[k] = v
    iris.p[-10003].hot = iris.p[-10005]


if __name__ == '__main__':
    print('network')
