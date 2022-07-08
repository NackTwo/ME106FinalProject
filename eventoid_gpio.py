# eventoid_gpio.py -- event checker for a single GPIO input pin.
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 22-Apr-2022 14:35

import machine, time
import eventoid

class EventoidGPIOPolled(eventoid.Eventoid):
    """EventoidGPIOPolled - generate events for rising/falling edges of a GPIO pin."""

    def __init__(self, eventer, edge_events, pin, data=None):
        """
        EventoidGPIOPolled() - eventoid object for polling rising/falling transitions of a GPIO pin
        
        eventer - Eventer maintaining the queue of generated events
        edge_events - tuple of (rising,falling) events to return
        pin - instance of machine.Pin to poll
        data - (optional) data to return with event
        """
        super().__init__(eventer, "gpio.polled", True)

        self.pin = pin
        (self.event_rising, self.event_falling) = edge_events
        self.data = data

        self.state_prev = pin.value()

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""
        return super().__repr__() + ",events=("+str(self.event_rising)+","+str(self.event_falling)+"),pin="+str(Pin)

    def poll(self):
        """ poll(): poll object for eventable conditions.  Returns True to Eventer if an event was queued, else False. """
        evented = False
        state_prev = self.state_prev

        b = self.pin.value()
        if b != state_prev:
            t = time.ticks_ms()
            if (self.event_rising is not None)  and (b == 1) and (state_prev == 0):
                self.eventer.add((self.event_rising,  t, self.data))
                evented = True
            if (self.event_falling is not None) and (b == 0) and (state_prev == 1):
                self.eventer.add((self.event_falling, t, self.data))
                evented = True

        self.state_prev = b
        return evented

# FIXME - this eventoid is a work-in-progress.  IT DON'T WORK
class EventoidGPIONonPolled(eventoid.Eventoid):
    """EventoidGPIOPolled - generate events for rising/falling edges of a GPIO pin using interrupts."""

    def __init__(self, eventer, edge_events, pin, data=None):
        """
        EventoidGPIOPolled() - eventoid object for detecting rising/falling transitions of a GPIO pin using interrupts
        
        eventer - Eventer maintaining the queue of generated events
        edge_events - tuple of (rising,falling) events to return
        pin - instance of machine.Pin to interrupt-enable
        data - (optional) data to return with event
        """
        super().__init__(eventer, "gpio.non-polled", False)

        self.pin = pin
        (self.event_rising, self.event_falling) = edge_events
        self.data = data

        mask =  0 if self.event_rising  is None else machine.Pin.IRQ_RISING
        mask |= 0 if self.event_falling is None else machine.Pin.IRQ_FALLING

        pin.irq(trigger=mask, handler=self._isr_gpio)

    def _isr_gpio(self, pin):
        g = pin.value()
        t = time.ticks_ms()

        if   (g == 0) and (self.event_falling is not None):
                self.eventer.add((self.event_falling, t, self.data))
        elif (g == 1) and (self.event_rising is not None):
                self.eventer.add((self.event_rising,  t, self.data))

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""
        return super().__repr__() + ",events=("+str(self.event_rising)+","+str(self.event_falling)+"),pin="+str(Pin)

    def poll(self):
        raise 
