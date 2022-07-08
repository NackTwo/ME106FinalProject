# eventoid_keypad.py -- event checker for matrix keypads
#
# This eventoid polls the keypad (rather than uses interrupts), and returns only
#   one keypad press or release at a time, by design.  Multiple (or all, if you have
#   a friend) keys can be held down simultaneously without issues.
#
# Note: to decrease the time spent in any one poll() call, we could poll just the next,
#       single row at a time and return quicker, but that level of performance/granularity
#       probably isn't necessary for most applications, given the nature of this device.
# Note: It probably wouldn't hurt to queue multiple press and release events in one call to poll()
#
# TODO: Implement and interrupt-driven eventoid that does *almost* the same thing.  It would likely
#       behave differently as some presses/releases wouldn't be noticed depending on the state of
#       other keys in the same row/column.
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 21-Apr-2022 18:35

from machine import Pin
import time, eventoid

class EventoidKeypadPolled(eventoid.Eventoid):
    def __init__(self, eventer, events, pinnums_rows, pinnums_cols, row_delay_ms=35):
        super().__init__(eventer, "keypad", True)

        (self.event_press,self.event_release) = events
        self.pinnums_rows = pinnums_rows
        self.pinnums_cols = pinnums_cols
        self.pins_cols    = [Pin(i, Pin.IN) for i in pinnums_cols]
        self.row_delay_ms = row_delay_ms

        self.prev_state   = []
        for i in range(len(self.pinnums_rows)):
            cols = [0 for i in pinnums_cols]
            self.prev_state.append(cols)

    def __repr__(self):
        return super().__repr__()+\
               ",events="+str((self.event_press,self.event_release))+",rows="+\
               str(self.pinnums_rows)+",cols="+str(self.pinnums_cols)

    def poll(self):
        _ = [Pin(n, Pin.IN) for n in self.pinnums_rows]
        pins_cols = self.pins_cols

        evented = False
        for (row,row_pinnum) in enumerate(self.pinnums_rows):
            Pin(row_pinnum, Pin.OUT, value=1)
            for (col, pinobj) in enumerate(pins_cols):
                val = pinobj.value()                   # 0=pressed, 1=unpressed
                if val == self.prev_state[row][col]:   # no change from prev scan, skip
                    continue

                if (self.event_press is not None) and (val == 1):
                        self.eventer.add((self.event_press, time.ticks_ms(), (row,col)))
                        evented = True
                elif (self.event_release is not None) and (val == 0):
                        self.eventer.add((self.event_release, time.ticks_ms(), (row,col)))
                        evented = True

                self.prev_state[row][col] = val

                if evented:
                    break
            Pin(row_pinnum, Pin.IN)
            if evented:
                break
            if self.row_delay_ms is not None:
                time.sleep_ms(self.row_delay_ms)

        return evented
