# Eventoid_timer.py -- event checker for a (restartable) timer
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 19-Apr-2022 13:17

from machine import Pin
import time, eventoid

class ExceptionTimerIncomplete(Exception):
    pass

class EventoidTimerPolled(eventoid.Eventoid):
    def __init__(self, eventer, event, periodic=False, period_ms=None, data=None):
        super().__init__(eventer, "timer.polled", True)

        self.event     = event
        self.periodic  = periodic
        self.period_ms = period_ms
        self.data      = data

        self.expiration = None

    def __repr__(self):
        return super().__repr__() + ",event="+str(self.event)+",periodic="+str(self.periodic)+",ms="+str(self.period_ms)+\
               ",exp="+str(self.expiration)+("" if self.data is None else "data="+str(self.data))

    def start(self, msecs=None, data=None):
        if msecs is None:
            if self.period_ms is None: raise ExceptionTimerIncomplete
            msecs = self.period_ms
        else:
            self.period_ms = msecs

        if data is not None:
            self.data = data
        self.expiration = time.ticks_add(time.ticks_ms(), msecs)

    def cancel(self):
        self.expiration = None

    def poll(self):
        if self.expiration is not None:
            t = time.ticks_ms()
            if time.ticks_diff(t, self.expiration) >= 0:
                self.eventer.add((self.event, t, self.data))
                self.expiration = time.ticks_add(t, self.period_ms) if self.periodic else None
                return True
        return False

# FIXME - this eventoid is a work-in-progress.  IT DON'T WORK
class EventoidTimerNonPolled(eventoid.Eventoid):
    def __init__(self, eventer, event, periodic=False, period_ms=None, data=None):
        super().__init__(eventer, "timer.non-polled", False)

        self.event     = event
        self.periodic  = periodic
        self.period_ms = period_ms
        self.data      = data

        self.timer     = None

    def __repr__(self):
        return super().__repr__() + ",event="+str(self.event)+",periodic="+str(self.periodic)+",ms="+str(self.period_ms)+\
               ","+("" if self.data is None else "data="+str(self.data))

    def start(self, msecs=None, data=None):
        """Set an (optionally periodic) timer at which time(s) an event is generated"""

        if self.timer is None:
            self.timer = machine.Timer(period=msecs,
                                       mode=(machine.Timer.PERIODIC if self.periodic else machine.Timer.ONE_SHOT),
                                       callback=self._isr_timer)
        else:
            raise EventerTimerInUseException()
        
    def cancel(self):
        if self.timer is not None:
            self.timer.deinit()
            self.timer = None
