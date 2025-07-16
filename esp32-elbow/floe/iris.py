import gc
# import struct

try:
    import uasyncio as asyncio
except ModuleNotFoundError:
    import asyncio
import floe.message
import json
import collections
from floe.timelord import TimeLord
import os
from floe.bifrost import Bifrost
# from floe.network import base_parameters



class Iris:
    def __init__(self):
        print('Iris initializing')
        self.globals = {'iris': self} # the globals to be used by eval functions
        self.p = {}                 # Parameter Table with no adr
        self.s = {}                 # Subscription List
        self.ss = {}                # Subscription from self inbox
        # {sub: pid, sub: (pid, arg)} !True anymore?
        self.t = TimeLord(self.p)
        
        # these are temporary until I figure out something better
        self.zorg = True
        self.locals = {'iris': self}
        
        self.bus = None             # can bus pid
        self.buss = {}            # moving to multiple busses soon
        
        self.ob = []                # Outbox
        self.obg = []               # Outbox generators
        
        self.webstuff = []          # Gui elements for web interface
        self.bifrost: Bifrost = Bifrost()
        
        self.core = None            # core element
        self.msg = floe.message.Message(iris=self)
        
        try:
            self.ib = collections.deque((), 40, True)  # micopython with max len and overflow protection
        except TypeError:
            self.ib = collections.deque([])

        # internal inbox currently unused
        # try:  # Internal mailbox
        #     self.iib = collections.deque((), 40, True)  # micopython with max len and overflow protection
        # except TypeError:
        #     self.iib = collections.deque([])

        ## I think these 2 will be depricated once async is fully implemented
        self.h = []  # Hardware to .chk()
        self.hw_outs = []  # Hardware outputs
        
        self.async_hw = [] # this is still unused, not sure if we care or not
        # self.chk = self.hw()

    def report(self):
        print('**** Parameter Table ****')
        for k, v in sorted(self.p.items()):
            print(k, str(type(v)).replace("<class '", '').replace("'>", ''))
        print('\n\n**** OUTBOX ****')
        for msg in self.ob:
            print(msg)
        # print('\n\n**** INTERNAL INBOX ****')
        # for msg in self.iib:
        #     print(msg)
        print('\n\n ********************** \n')

    def save_states(self):
        return {k: [v.state, v.blob] for k, v in self.p.items()}

    def hw_iter(self):
        while True:
            for hw in self.h:
                yield hw

    def send(self, *, pid, load, type=0, adr=None, is_generator=False) -> None:
        """ add to outbox """
        if adr is not None:
            # print('adr is not none', pid, adr, w)
            h = self.bus.header.pack(type=type, pid=pid, adr=adr)
        else:
            h = self.bus.header.pack(type=type, pid=pid, adr=self.bus.header.adr)
        # print('sending message: {} to outbox'.format(m))

        # put message in sorted order min lowest
        if is_generator:
            self.obg.append((h, load))
            return
        if len(self.ob) < 20:
            # TODO there is an overflow condition when bus is not working, fix this
            self.ob.append((h, load))

    def send_i(self, m) -> None:
        """ add to internal mailbox """
        self.iib.append(m)

    async def cob(self):
        """ check outbox """
        while True:
            if self.ob:
                if self.bus.rts():
                    # print('sending message')
                    h, load = self.ob.pop(0)
                    self.bus.send(load, h)
            elif self.obg:  #outbox generators
                if self.bus.rts():
                    try:
                        load = next(self.obg[0][1])
                        h = self.obg[0][0]
                        self.bus.send(load, h)
                    except StopIteration:
                        print('done sending')
                        self.obg.pop(0)            
            await asyncio.sleep(.02)

    async def cib(self):
        """ check inbox """
        while True:
            if self.ib:
                msg_func, sub, load = self.ib.popleft()
                # self.msg.process(h=sub, load=load)
                msg_func(load, sub)
            await asyncio.sleep(0)

    # def ciib(self):
    #     """ check internal inbox """
    #     # TODO: harmonize with cib
    #     # self subscription format: {pid: sender: pid: receiver} || {pid: sender: (pid: receiver, args: any)}
    #     if self.iib:
    #         pid, load = self.iib.popleft()
    #         sub = self.ss[pid]
    #         if type(sub) is floe.message.Functor:
    #             if type(sub.pid) is tuple:
    #                 for s in sub.pid:
    #                     self.p[s](sub.arg)
    #             else:
    #                 self.p[sub.pid](sub.arg)

    #         elif type(sub) is tuple:
    #             self.p[sub](load, *sub)
    #         else:
    #             self.p[sub](load)

    def add_bus(self, label, bus):
        self.bus = bus
        
        self.buss[label] = bus

    def subscribe(self, header: int|str, pid: int, bundle: str):
        self.bus.subscribe(header)
        self.s[header] = (pid, bundle)
    
    def unsubscribe(self, header):
        self.bus.unsubscribe(header)
        self.s.pop(header)

    def add_hots(self, all_hots: dict[str, list[int]]):
        for pid, hots in all_hots.items():
            for hot in hots:
                self.p[int(hot)].add_hot(pid)

    def boot(self, start_mailboxes=False):
        for param in self.p.values():
            param.update()
        if start_mailboxes:
            loop = asyncio.get_event_loop()
            loop.create_task(self.cib())
            loop.create_task(self.cob())
    
    def create_subs(self):
        if 'subscriptions.json' not in os.listdir():
            return
        
        adr = str(self.bus.header.adr)
        with open('subscriptions.json', 'r') as f:
            subs = json.load(f)

        if adr not in subs.keys():
            print('no subscriptions')
            return
        for sub in subs[adr]:
            self.s[sub[0]] = (sub[1], sub[2]) 
            print(sub)


if __name__ == '__main__':
    print('iris test')
    # iris = Iris(adr=36, fault_bits=8, header_bits=29, ad_bits=10, priority_bits=3)
    # print(test := iris.msg.unpack(472186874))
    # print(iris.msg.pack(**test))

