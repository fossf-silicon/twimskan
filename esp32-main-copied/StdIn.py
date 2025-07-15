"""
StdIn reads lines from stdin
"""

from floe import implementation
from Parameter import Parameter

import sys, collections, io
import uselect

try:
    import uasyncio as asyncio
except:
    import asyncio

esp32 = False
try:
    
    import utime
    if not implementation.wasm:
        print('we have esp32')
        esp32 = True
except:
    pass


#######################
# repl
#######################

def do_repl(code: str, iris):
    print('repling', code)
    code.replace('<br>', '\n')
    code.replace('&nbsp;', ' ')
    try:
            _return = str(eval(code, globals(), iris.locals)).strip('<>')
            return f">>> {code}\n{_return}"

    except SyntaxError:
        try:
            exec(compile(code, 'input', 'single'), globals(), iris.locals)

            return f">>> {code}"
        except Exception as e:
            # print(e)
            thing = io.StringIO()
            sys.print_exception(e, thing)
            # print(thing.getvalue())
            exc = thing.getvalue()  # .replace('\n', '<br>')
            return f">>> {code}\n{exc}"


    except Exception as e:
        # print(e)
        thing = io.StringIO()
        sys.print_exception(e, thing)
        # print(thing.getvalue())
        exc = thing.getvalue()  # .replace('\n', '<br>')
        return f">>> {code}\n{exc}"



class StdIn(Parameter):
    struct = 'u'  # string
    
    def __init__(self, iris, buf_len=40, send2repl=True, **k):
        super().__init__(iris=iris, **k)
        self.repl = send2repl
        self.iris = iris
        
        if esp32:
            self.spoll=uselect.poll()
            self.spoll.register(sys.stdin,uselect.POLLIN)
        
        try:
            self.buffer = collections.deque((), buf_len, True)  # micopython with max len and overflow protection
            
        except TypeError:
            self.buffer = collections.deque([])
        
    def update(self):
        super().update()
        if esp32:
            print('beginning loop')
            loop = asyncio.get_event_loop()
            loop.create_task(self.chk())

    def read(self):
        while self.spoll.poll(0):                      
                char = sys.stdin.read(1)
                if char is None:
                    return

                if char == '\n':
                    
                    l = len(self.buffer)
                    line = ''.join((self.buffer.popleft() for _ in range(len(self.buffer))))
                    if not len(line):
                        return 
                    self.state = line
                    self.send()
                    if self.repl:
                        print(do_repl(self.state, self.iris))
                    return
    
                self.buffer.append(char)   
        
    async def chk(self):
        while True:
            # print('b4read')
            self.read()
            # print('afterread')
            await asyncio.sleep_ms(100)
    

