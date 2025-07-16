import heapq
from heapq import heappop, heappush, heapify


try:
    from utime import ticks_ms as now
except:
    import time
    def now():
        return int(time.monotonic() * 1000)


class TimeLord:
    def __init__(self, p: dict[int, any]):
        self.t = []
        heapify(self.t)
        self.p = p
        self.lc = now() # last checked time
        self.oflw = []  # place to store timers that ding after rollover

    def add_tim(self, timer: tuple[int, any]) -> None:
        heappush(self.t, timer)

    # ------------------------------------------------------------------------

    def add_tim_oflw(self, timer: tuple[int, any]):
        self.oflw.append(timer)

    # ------------------------------------------------------------------------

    def rem_tim(self, timer: tuple[int, any]) -> None:
        # remove a timer
        try:
            self.t.remove(timer)
        except ValueError:
            try:
                self.oflw.remove(timer)
            except ValueError:
                pass
        heapify(self.t)

    # ------------------------------------------------------------------------

    def chk(self) -> None:
        """Check the timers"""
        if not self.t:
            return

        _now = now()
        if _now < self.lc:  # check for rollover
            self.process_rollover()

        self.lc = _now
        if self.t[0][0] < now():
            _, timer = heappop(self.t)
            timer.send()

    # ------------------------------------------------------------------------

    def process_rollover(self):
        while True:  # process the entire queue
            try:
                _, timer = heappop(self.t)
                timer.send()
            except IndexError:
                break
        self.t.extend(self.oflw)
        heapify(self.t)