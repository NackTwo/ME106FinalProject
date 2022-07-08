from neopixel import Neopixel

class Light:

    _NEOBRIGHTNESS_MAX = const(255)
    _NEOPIXELS         = const(1)
    _DUTY_DECREMENT    = const(10)

    def __init__(self, pinnum_neo, color_order, sm_num, duty=0, color=None):
        self.neo   = Neopixel(_NEOPIXELS, sm_num, pinnum_neo, color_order)
        self.duty  = duty
        self.color = (255,255,255) if color is None else color
        self.set_duty(duty, color)
        
    def set_duty(self, duty, color=None):
        self.duty = duty
        if color is not None: self.color = color

        self.neo.brightness((_NEOBRIGHTNESS_MAX*duty)/100)
        self.neo.set_pixel(0, self.color)
        self.neo.show()

    def set_color(self, color):
        self.set_duty(self.duty, color)
        
    def get_duty(self): return self.duty

    def on(self, color=None):
        self.set_duty(100, color=color)

    def off(self, color=None):
        self.set_duty(0, color=color)

    def dim(self, f=None):
        if f:
            self.set_duty(min(100, max(0, f(self))))
        else:
            self.set_duty(min(100, max(0, self.duty-_DUTY_DECREMENT)))

    def show(self):
        self.set_duty(self.duty)
