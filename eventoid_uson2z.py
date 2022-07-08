# EventoidUsonic2Zone.py -- event checker for two zone-thresholded ultrasonic sensor:
#
# NB: The worst-case time that it takes to poll using this eventoid is the time that it takes
#     for the ranging function to time-out and finally give up.
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 18-Apr-2022 12:24

from machine import Pin
import time, eventoid

USONIC_2ZONES_FAR   = 2
USONIC_2ZONES_OUTER = 1
USONIC_2ZONES_INNER = 0

class EventoidUsonic2ZonesPolled(eventoid.Eventoid):
    def __init__(self, eventer, usonic, range_window, zones, hysteresis_mm, debug):
        super().__init__(eventer, "uson2z", True)

        self.usonic = usonic
        (self.mm_min, self.mm_max) = range_window
        (self.mm_boundary_outer, self.events_outer) = zones[0]
        (self.mm_boundary_inner, self.events_inner) = zones[1]
        self.mm_hysteresis = hysteresis_mm
        self.debug         = debug

        if debug:
            self.mm_last = range_window[1] + hysteresis_mm + 1  # just into FAR
        self.zone_last = USONIC_2ZONES_FAR

    def __repr__(self):
        return super().__repr__() +\
               ",range="+str(self.range_window)+",zones="+str(self.zones)+\
               ",hyst="+str(self.hysteresis_mm+","+str(debug))

    def _usonic_get_zone(self):
        mm = self.usonic.range_mm()

        if (mm < self.mm_min) or (mm > self.mm_max):  # toss all "unreliable" values
            return None

        if self.debug is not None:  # only print if enabled and movement above threshold
            if abs(mm - self.mm_last) > self.debug:
                print(mm, "mm")
            self.mm_last = mm
            
        zone_last = self.zone_last
        mm_outer  = self.mm_boundary_outer
        mm_inner  = self.mm_boundary_inner
        mm_hyster = self.mm_hysteresis

        if zone_last == USONIC_2ZONES_FAR:
            if   mm > (mm_outer-mm_hyster): ret_zone = USONIC_2ZONES_FAR
            elif mm > mm_inner:             ret_zone = USONIC_2ZONES_OUTER
            else:                           ret_zone = USONIC_2ZONES_INNER
        elif zone_last == USONIC_2ZONES_OUTER:
            if   mm > (mm_outer+mm_hyster): ret_zone = USONIC_2ZONES_FAR
            elif mm > (mm_inner-mm_hyster): ret_zone = USONIC_2ZONES_OUTER
            else:                           ret_zone = USONIC_2ZONES_INNER
        else:
            if   mm < (mm_inner+mm_hyster): ret_zone = USONIC_2ZONES_INNER
            elif mm > mm_outer:             ret_zone = USONIC_2ZONES_FAR
            else:                           ret_zone = USONIC_2ZONES_OUTER

        return (ret_zone, mm)

    # TODO/FIXME: there's an ugly division of labor between this function and _usonic_get_zone
    #   that could use some cleaning-up
    # Note: it takes about 15ms to call _usonic_get_zone(), so this will block for that long
    def poll(self):
        if (z := self._usonic_get_zone()) is None: return False
        z,mm = z
        if z == (zone_last := self.zone_last): return False

        t = time.ticks_ms()
        evented = False

        if zone_last == USONIC_2ZONES_FAR:
            self.eventer.add((self.events_outer[0], t, mm))
            if z == USONIC_2ZONES_INNER:
                self.eventer.add((self.events_inner[0], t, mm))
        elif zone_last == USONIC_2ZONES_OUTER:
            if z == USONIC_2ZONES_FAR:
                self.eventer.add((self.events_outer[1], t, mm))
            else:
                self.eventer.add((self.events_inner[0], t, mm))
        else: # zone_last == USONIC_2ZONES_INNER
            self.eventer.add((self.events_inner[1], t, mm))
            if z == USONIC_2ZONES_FAR:
                self.eventer.add((self.events_outer[1], t, mm))

        self.zone_last = z
        return True
