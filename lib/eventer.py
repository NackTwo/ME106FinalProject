# The Eventer class(es) encapsulates all of the event checking and systhesis,
#    separate from the state machine implementation code.
#
# Note that any time that the event queue is manipulated, interrupts must be turned
#   off to prevent it from being corrupted by interrupt-induced race conditions.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 25-Apr-2022 22:55

import micropython, machine, time

micropython.alloc_emergency_exception_buf(100)

class StateMachineException(Exception):
    pass

class EventoidException(Exception):
    pass

class EventerException(Exception):
    pass

class Eventer:
    """
    Custom event manager that composes events from changing conditions in the system
    and queues them up for retrieval, usually by a state machine.
    """

    def __init__(self, trace=False, trace_info=None):
        """
        Create an event-checker object with an internal queue for holding pending events.

        trace - (optional) turn on trace messages to the console [type: bool]
        trace_info - (optional) tuple of two dictionaries containing mapping of state and/or
                     event values to strings.  If None or either tuple member is None, then str(val)
                     will be used instead.
                     [type: None | (None|dict(state_val, str), None|dict(event_val, str))]
        """
        self.trace = trace
        (self.state_str, self.event_str) = (None, None) if trace_info is None else trace_info

        self._queue            = list()
        self._requires_polling = 0
        self._next_id          = 0
        self.eventoids         = dict()

    def register(self, eo):
        id = self._next_id
        self.eventoids[id] = eo

        eo.set_queue(self._queue)
        if eo.is_polled():
            self._requires_polling += 1
        self._next_id += 1

    # FIXME: this is entirely untested
    def unregister(self, id):
        if self.eventoids.get(id) is None:
            raise EventerException("No such eventoid id: "+str(id))

        eo = self.eventoids[id]
        if eo.is_polled:
            self._requires_polling -= 1
        eo.deinit()
        del self.eventoids[id]

    def requires_polling(self):
        return bool(self._requires_polling)

    def poll(self):
        """
        Poll all of the eventoids that requrie it for changes since last called.
        The order in which they are checked/queued implicitly dictates their priority,
          which is the order in which they were registered.
        The current implementation only allows one (polled) event to be queued at a time because
          this helps to limit race conditions in users' programs that are very difficult to defend against --
          one example being the race between pressing a button to cancel a timer and the timer going
          off anyways.
        
        params: none
        """
        if self._requires_polling == 0:
            return
        for eo in self.eventoids.values():
            if eo.is_polled():
                if eo.poll():    # one and done
                    return

    def add(self, e):
        """Put an event in the queue for subsequent removal"""
        mask = machine.disable_irq()
        self._queue.append(e)
        machine.enable_irq(mask)

    def next(self):
        """
        Retrieve the next event (Event.*) from the queue of pending events.
        Returns Event.NONE if the queue is empty.


        params: none
        """
        mask = machine.disable_irq()        # prevent queue corruption
        e = self._queue.pop(0) if len(self._queue) else None
        machine.enable_irq(mask)

        return e

    def loop(self, process_func, state):
        """
        Run the state machine in a (infinite) loop.
        process_func - function to process the current (state,event) and returt the new state
                       [type: state_new = process_func(event, event_msecs, event_data)]
        state - the state in which the state machine starts [type: any]
        """
        trace     = self.trace
        state_str = self.state_str
        event_str = self.event_str

        if self.trace:
            print(state if state_str is None else state_str[state])

        while True:
            if self.requires_polling():
                self.poll()

            if (e := self.next()) is not None:
                (event, event_time, event_data) = e
                if self.trace:
                    if event_str is None:
                        s = str(event)
                    else:
                        s = event_str[event]
                        if s is None: s = str(event)

                    print(f"{s}:{event_time}", end="")
                    if event_data is not None:
                        print(f":{event_data}", end="")

                state_new = process_func(state, event, event_time, event_data)

                if trace:
                    print(" -> ", end="")
                    if state_str is None:
                        s = str(state_new)
                    else:
                        s = state_str.get(state_new)
                        if s is None: s = str(state_new)
                    print(s)
                state = state_new

    def err_bad_event_in_state(self, st, e, data):
        try:
            e_str = self.event_str[st]
        except:
            e_str = "Event#"+str(e)
        raise StateMachineException("Unrecognized "+e_str+" in "+self.state_str[st])

    def err_unexpected_event(self, st, e, data):
        try:
            e_str = self.event_str[e]+":"+str(data)
        except:
            e_str = "Event#"+str(e)+":"+str(data)
        raise StateMachineException("Unexpected "+e_str+" in "+self.state_str[st])

    def err_bad_state(self, st):
        try:
            s = STATE_STR[st]
        except:
            s = "State#"+str(st)
        raise EventerException("Undefined or unhandled State#"+str(st))
