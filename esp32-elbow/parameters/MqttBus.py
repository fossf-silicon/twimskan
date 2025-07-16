import paho.mqtt.client as mqtt  # import the client
# from floe.parameters import Parameter
#  from floe.mqtt_header import MqttHeader
import floe
from floe.iris import FP
from random import randint
# https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/
# mosquitto_pub -d -t testTopic -m "Hello world!"
# mosquitto_sub -d -t '#'

# Future Note:: network structure
# ORG/CanvID/DeviceID/[...]


class MqttHeader:
    def __init__(self, *, adr: int, fault_bits, s, packet_size=50, **k):
        """
        package [adr][parameter bits]
        """
        self.s = s
        self.adr = str(adr)
        self.int_adr = adr
        self.fault = 2 ** fault_bits
        self.packet_size = packet_size
        

    @staticmethod
    def unpack(h: str) -> tuple[int, int, int, str]:
        """
        unpack int header into write bit, address and pid
        return tuple(write, address, pid)
        """
        adr, pid, type = h.split('/')
        adr = int(adr)
        pid = int(pid)
        type = int(type)
        return (
            adr,  # adr
            pid,
            type
        )

        
    @staticmethod
    def pack(type: int, pid: int, adr: int) -> str:
        # print('packing', adr, pid, type)
        return f'{adr}/{pid}/{type}'

class MqttBus:
    def __init__(self, *, pid, broker_adr, client_name, self_adr, fault_bits, iris, debug=False, **k):
        self.pid = int(pid)
        self.broker_adr = broker_adr
        self.client = mqtt.Client(client_name + str(randint(1, 10000000)))
        self.header = MqttHeader(adr=self_adr, fault_bits=fault_bits, s=iris.s)
        self.debug = debug
        self.ib = iris.ib
        self.s = iris.s
        self.msg = iris.msg
        
        # outbox stuff
        self.ob = []
        self.obg = []
        
        self.bifrost = None
        import config
        if config.webserver_debug:
            print('making bifrost: connecting to MQTT')
            self.bifrost = floe.bifrost
            
        iris.p[self.pid] = self

    def connect(self):
        self.client.on_message = self.process4ib
        self.client.connect(self.broker_adr)
        self.subscribe('0/#')  # network subs
        self.subscribe('#')
        self.subscribe(f'{self.header.adr}/#')  # subscribe to self        self.client.loop_start()
        self.client.loop_start()

    def subscribe(self, topic):
        self.client.subscribe(topic)
        
    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    @staticmethod
    def rts():
        return True

    def process4ib(self, client: mqtt.Client, userdata, msg) -> None:
        """
        sends message to iris' inbox
        """
        print('got message', msg.topic, msg.payload)
        if self.bifrost is not None:
            # print('sending to bifrost')
            self.bifrost.send({'cmd': 'post', 'msg': f'MQTT: {msg.topic}, {msg.payload}'})
        try:
            adr, pid, type = self.header.unpack(msg.topic)
        except:
            print("message doesn't fit standard")
        
        do_func, sub_pid = self.msg.want(adr, pid, type, msg.topic, self.header.int_adr)
        if do_func is not False:    
            self.ib.append((do_func, sub_pid, msg.payload))

    def send(self, load, h):
        self.client.publish(topic=h, payload=load)
        
    def cob(self):
        """check self outbox if ready to send message"""
        if self.ob:
            h, load = self.ob.pop(0)
            self.send(load, h)
        elif self.obg:
            try:
                load = next(self.obg[0][1])
                h = self.obg[0][0]
            except StopIteration:
                print('done sending')
                self.obg.pop(0)
                
    def update(self):
        for attr, val in self.__dict__.items():
            if isinstance(val, FP):
                self.__dict__[attr] = self.iris.p[val.pid]


if __name__ == '__main__':
    print('two')
    from floe import iris
    import time

    print('one')
    header = MqttHeader(adr=123, fault_bits=10, s=iris.s)
    client = MqttBus('localhost', 'test', header, ib=iris.ib, debug=True)
    client.connect()
    client.subscribe('0/#')  # nwk sub
    client.subscribe(f'{client.header.adr}/#')  # self sub
    client.subscribe('#')
    subs = {
        '234/567': (123, 456)
    }
    for sub, val in subs.items():
        client.subscribe(sub)
        iris.s[sub] = val
    client.client.publish('123/4567', '456')
    count = 0
    print('loaded')
    while True:
        time.sleep(2)
        count += 1
        print(count)
