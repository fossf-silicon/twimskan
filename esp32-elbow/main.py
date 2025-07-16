import floe
import os, gc
import uasyncio as asyncio
import machine
machine.freq(240000000)


import factory.factory as factory
factory.boot()


iris = floe.Iris()

import config.basic
def main():
    config.basic.setup(iris)

    for k, v in iris.p.items():
        print(k, v)

test_script = [
    {'cmd': 'message1'},
    {'cmd': 'message4'},
    {'cmd': 'load', 'script': 'test.evzr'},
    {'cmd': 'message4'},
    {'cmd': 'message5'}
]


main()
iris.boot(start_mailboxes=True)
iris.core.boot()


loop = asyncio.get_event_loop()
loop.create_task(iris.cob())
gc.collect()
loop.run_forever()
