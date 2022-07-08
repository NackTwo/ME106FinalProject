# The Eventoid class is the superclass of all of the Eventer plug-ins
#   Eventoids do the following things:
#   1. they get created (first, obviously)
#   2. they (minimally) communicate with the Eventer to which they're registered
#   3. they are asked to poll, and report back with True/False if they queued any events
#   4. TODO: someday they might be asked to clean-up via deinit() if unregistered
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 22-Apr-2022 17:38

class Eventoid:

    def __init__(self, eventer, eo_type, requires_polling):
        self.eventer = eventer
        self.eo_type = eo_type           # not used for anything (yet?)
        self._polled  = requires_polling

        self.event_queue = None

    def __repr__(self):
        return "type="+self.eo_type+","+str(self._polled)

    def is_polled(self):
        return self._polled

    def set_queue(self, event_queue):
        self.event_queue = event_queue

    # method for subclasses that use require polling rather than solely relying on interrupts
    def poll(self): pass

    # currently unused method for cleaning up when unregistered from the Eventer.
    def deinit(self): pass
