# demo_gpio3.py: demo of interrupt-driven GPIO eventoid
#
# Demonstration of the flexibility of associating unique events on multiple
# GPIO eventoid instances, arbitrarily on rising and/or falling edges.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 17:00

import time
from machine import Pin, PWM, I2C
from sm_light import Light
import hc_sr04_edushields
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

from eventer import Eventer
from eventoid_gpio import EventoidGPIONonPolled
from eventoid_timer  import EventoidTimerPolled
from eventoid_uson2z import EventoidUsonic2ZonesPolled

'''
    STATE MACHINE SETUP
'''

TRACE_STATES = True

#Neopixel RGB
PIN_NEOPIXEL = const(28)    # the Neopixel is now the light source
ORDER_colorS = "GRB"        # this WS2812B flavor takes green, red, then blue data
SM_NEOPIXEL  = const(0)     # which PIO-SM to use (needed by neopixel library)

COLOR_RED    = (255,   0, 0)
COLOR_YELLOW = (255, 150, 0)
COLOR_GREEN  = (  0, 255, 0)

#Pins linked to event triggers
PIN_BUTTON_D = const(2)
PIN_BUTTON_AST = const(5)

# States of the state machine
STATE_SLEEP           = const(0)
STATE_INPUT           = const(1)
STATE_WAIT_FOR_VESSEL = const(2)
STATE_FILLING         = const(3)
STATE_STR   = { STATE_SLEEP:              'STATE_SLEEP',
                STATE_INPUT:              'STATE_INPUT',
                STATE_WAIT_FOR_VESSEL:    'STATE_WAIT_FOR_VESSEL',
                STATE_FILLING:            'STATE_FILLING'}

# Events returned from all of our eventoids
EVENT_PRESS_D          = const(0)
EVENT_PRESS_AST        = const(1)
EVENT_SCAN_TIMER       = const(2)
EVENT_ENTERING_OUTER   = const(3)  # occurs when entering OUTER from FAR
EVENT_EXITING_OUTER    = const(4)  # occurs when exiting  OUTER into FAR
EVENT_ENTERING_INNER   = const(5)  # occurs when entering INNER from OUTER
EVENT_EXITING_INNER    = const(6)  # occurs when exiting  INNER into OUTER

EVENT_STR   = { EVENT_PRESS_D:        'EVENT_PRESS_D',
                EVENT_PRESS_AST:      'EVENT_PRESS_AST',
                EVENT_SCAN_TIMER:     'EVENT_SCAN_TIMER',
                EVENT_ENTERING_OUTER: 'EVENT_ENTERING_OUTER',
                EVENT_EXITING_OUTER:  'EVENT_EXITING_OUTER',
                EVENT_ENTERING_INNER: 'EVENT_ENTERING_INNER',
                EVENT_EXITING_INNER:  'EVENT_EXITING_INNER'}

PIN_USON_TRIGGER = const(11)   # The Seeed/Grove sensor only has one pin
PIN_USON_ECHO    = const(10)

DISTANCE_OUTER_MM         = const(150)  # mm to outer/warning zone
DISTANCE_INNER_MM         = const(-100)  # mm to inner/danger  zone
DISTANCE_RANGE_CUTOFFS_MM = (0, 10000) # toss all ultrasonic values outside of this range
DISTANCE_HYSTERESIS_MM    = const(5)    # hysteresis band on each side of inner/outer distance values
DISTANCE_DEBUG_MM         = None        # movement threshold in mm to test ranging, or None to turn off

usonic = hc_sr04_edushields.HCSR04(PIN_USON_TRIGGER, PIN_USON_ECHO)
light  = Light(PIN_NEOPIXEL, ORDER_colorS, SM_NEOPIXEL, duty=0)

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

#                                               (rising,falling) edge event(s)         the GPIO Pin
eo_btn_d    = EventoidGPIONonPolled(eventer, (None,EVENT_PRESS_D),                     Pin(PIN_BUTTON_D, Pin.IN))
eo_btn_ast  = EventoidGPIONonPolled(eventer, (None,EVENT_PRESS_AST),                   Pin(PIN_BUTTON_AST, Pin.IN))
eo_timer    = EventoidTimerPolled(eventer, EVENT_SCAN_TIMER)
eo_uson2z = EventoidUsonic2ZonesPolled(eventer, usonic, DISTANCE_RANGE_CUTOFFS_MM,
                    ( (DISTANCE_OUTER_MM, (EVENT_ENTERING_OUTER,EVENT_EXITING_OUTER)),
                      (DISTANCE_INNER_MM, (EVENT_ENTERING_INNER,EVENT_EXITING_INNER)) ),
                    DISTANCE_HYSTERESIS_MM,
                    DISTANCE_DEBUG_MM)
_ = eventer.register(eo_btn_d)
_ = eventer.register(eo_btn_ast)
_ = eventer.register(eo_timer)
_ = eventer.register(eo_uson2z)


'''
    TIMERS
'''
SLEEP_TIME_MSECS = const(5000)    #5s auto shut off timer for LCD screen
SCAN_MSECS       = const(250)     #0.25s Intervals for checking whether a key has been pressed



'''
    SPEAKER RELATED CODE
'''
#Define Speaker consstant GP18 on baseboard
PIN_SPEAKER = const(18)
PWM_MAX = const((2**16)-1)
speaker = PWM(Pin(PIN_SPEAKER))

ERROR_NOTE = const(493)
BUTTON_NOTE = const(440)
ENTER_NOTE = const(880)

def speaker_press():
    speaker.freq(BUTTON_NOTE)
    speaker.duty_u16(PWM_MAX//2)
    
def speaker_error():
    speaker.freq(ERROR_NOTE)
    speaker.duty_u16(PWM_MAX//2)
    time.sleep(0.0625)
    speaker.duty_u16(0)
    time.sleep(0.0625)
    speaker.duty_u16(PWM_MAX//2)    #Buzzer plays double beep to inform user of error

#def speaker_confirm():
    



'''
    KEYPAD RELATED CODE
'''

# Define keypad constants
KEY_UP = const(0)
KEY_DOWN = const(1)

keys = [['1', '2', '3', 'A'],
        ['4', '5', '6', 'B'],
        ['7', '8', '9', 'C'],
        ['*', '0', '#', 'D']]

# Assign rows and columns to the Pico
rows = [9, 8, 7, 6]
cols = [5, 4, 3, 2]

row_pins = [Pin(GP, Pin.OUT) for GP in rows]
col_pins = [Pin(GP, Pin.IN, Pin.PULL_DOWN) for GP in cols]

def keypad_init():
    for row in range(0,4):
        for col in range(0,4):
            row_pins[row].low()

def scan(row,col):
    # Scan the keypad

    #Set current column on
    row_pins[row].high()
    key = None
    
    #Check if key is pressed
    if col_pins[col].value() == KEY_DOWN:
        key = KEY_DOWN
    if col_pins[col].value() == KEY_UP:
        key = KEY_UP
    row_pins[row].low()
    
    #Return key pressed
    return key

# Init list of from values inputted by keypad
valuelist = []
finalvalue = None



'''
    LCD RELATED CODE
'''

PIN_DISP_SCL = const(1)
PIN_DISP_SDA = const(0)

disp_scl = Pin(PIN_DISP_SCL)
disp_sda = Pin(PIN_DISP_SDA)

I2C_CHANNEL = const(0)
I2C_FREQ    = const(400000)

I2C_ADDR     = 0x27
I2C_NUM_ROWS = 4
I2C_NUM_COLS = 20

i2c = I2C(I2C_CHANNEL, scl=disp_scl, sda=disp_sda, freq=I2C_FREQ)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

def disp_welcome():
    lcd.putstr("Welcome!")
    lcd.move_to(0,1)
    lcd.putstr("Push * To Begin")
    
#When 'Wake' button is pushed, prompt user to enter amount
def disp_prompt():
    speaker.freq(ENTER_NOTE)
    speaker.duty_u16(PWM_MAX//2)
    lcd.backlight_on()
    lcd.clear()
    lcd.putstr("Enter Amount")
    lcd.move_to(0,1)
    lcd.blink_cursor_on()

#When 'Enter' button is pushed, display confirmation on LCD screen
def disp_confirm(finalval):
    lcd.clear()
    lcd.blink_cursor_off()
    lcd.hide_cursor()
    lcd.putstr(str(finalval) + 'oz Confirmed')
    lcd.move_to(0,1)
    lcd.putstr('Place Cup')
    speaker.freq(ENTER_NOTE)     #Single confirm Beep
    speaker.duty_u16(PWM_MAX//2)
    time.sleep(0.25)
    speaker.duty_u16(0)
    
#When 'Enter' button is pushed and inputted value is > limit, display limit
def disp_limit(finalval):
    lcd.clear()
    lcd.blink_cursor_off()
    lcd.hide_cursor()
    lcd.putstr(str(finalval) + 'oz Limit')
    lcd.move_to(0,1)
    lcd.putstr('Place Cup')
    speaker.freq(ENTER_NOTE)     #Double Beep
    speaker.duty_u16(PWM_MAX//2)
    time.sleep(0.0625)
    speaker.duty_u16(0)
    time.sleep(0.0625)
    speaker.duty_u16(PWM_MAX//2)
    time.sleep(0.125)
    speaker.duty_u16(0)

#save timestamp of power on for lcd auto sleep feature
wake_time = time.ticks_ms()



'''
    PUMP RELATED CODE
'''
PUMP_PIN = const(16)
pump = Pin(PUMP_PIN, Pin.OUT)




'''
    FLOWMETER RELATED CODE
'''

# GP PIN
FLOW_PIN = const(15)
FLOW_TIME_INC = 250 #MSEC

flowPin = Pin(FLOW_PIN, Pin.IN)
#flowPin.on()

flowTime = 0
totalFlow = 0

def flow(pin):
    global count
    count += 1

def scan_flow():
    global count
    global FLOW_TIME_INC
    global flowTime
    global totalFlow
    global finalvalue
    count = 0
    time.sleep_ms(FLOW_TIME_INC//2)
    # Calculates waterflow within the past .25 seconds from time.sleep
    flowRate = (count * 2.25)
    flowTime += FLOW_TIME_INC
    totalFlow += flowRate
    totalFlowoz = totalFlow/29.574
    print("flowRate is {:.3f} ml/s Time elasped is {:.2f} Total flow is {:.3f} oz".format(flowRate, flowTime, totalFlowoz))
    return totalFlowoz

flowPin.irq(trigger=Pin.IRQ_RISING, handler=flow)


'''
    USON RELATED CODE
'''

# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    global wake_time
    global count
    global FLOW_TIME_INC
    global flowTime
    global totalFlow
    global finalvalue
    if state == STATE_SLEEP:
            if event == EVENT_SCAN_TIMER:
                                if time.ticks_diff(time.ticks_ms(),wake_time) >= SLEEP_TIME_MSECS:     #Auto-Sleeps LCD screen if idle for 5 seconds
                                    lcd.backlight_off()
                                else:
                                    pass
                                for row in range(4):
                                    for col in range(4):
                                        key = scan(row, col)
                                        if key == KEY_DOWN:
                                            lcd.backlight_on()
                                            wake_time = time.ticks_ms()
                                eo_timer.start(SCAN_MSECS)
                                return STATE_SLEEP
            elif event == EVENT_PRESS_AST:
                                disp_prompt()
                                return STATE_INPUT
            elif event == EVENT_PRESS_D:
                                return STATE_SLEEP
            elif event == EVENT_EXITING_OUTER:
                                return STATE_SLEEP
            elif event == EVENT_ENTERING_OUTER:
                                return STATE_SLEEP
            else:
                                eventer.err_unexpected_event(state, event, event_data)
    elif state == STATE_INPUT:
            if event == EVENT_SCAN_TIMER:
                                speaker.duty_u16(0)
                                for row in range(4):
                                    for col in range(4):
                                        key = scan(row, col)
                                        if key == KEY_DOWN:
                                            #print('Key Pressed:', keys[row][col])
                                            last_key = keys[row][col]
                                            if last_key == "#":                          #Clears input values
                                                valuelist.clear()
                                                lcd.move_to(0,1)
                                                lcd.putstr("  ")
                                                lcd.move_to(0,1)
                                                speaker.freq(BUTTON_NOTE)
                                                speaker.duty_u16(PWM_MAX//2)
                                            elif last_key == "*":                        #We do not want this as an input
                                                pass
                                            elif last_key == "A":                        #Press A for 8oz Preset
                                                finalvalue = 8
                                                disp_confirm(finalvalue)
                                            elif last_key == "B":                        #Press B for 16oz Preset
                                                finalvalue = 16
                                                disp_confirm(finalvalue)
                                            elif last_key == "C":                        #Press C for 32oz Preset
                                                finalvalue = 32
                                                disp_confirm(finalvalue)
                                            elif last_key == "D":                        #Press D as Enter Key
                                                if valuelist == []:                      #If no input, Set D to 64oz Preset 
                                                    finalvalue = 64
                                                    disp_confirm(finalvalue)
                                                else:                                    #Confirm Input
                                                    finalvalue = int(''.join(valuelist))
                                                    if finalvalue >= 64:                 #Max limit is 64oz
                                                        finalvalue = 64
                                                        disp_limit(finalvalue)
                                                    else:    
                                                        disp_confirm(finalvalue)
                                            elif len(valuelist) >= 2:                    #Prevents user from inputting more than 2 digits
                                                print('Digit Limit Reached')
                                                speaker_error()
                                            else:
                                                valuelist.append(last_key)     #Add inputted digit to list of values to later convert to value
                                                lcd.putstr(last_key)
                                                speaker_press()
                                eo_timer.start(SCAN_MSECS)
                                return STATE_INPUT
            elif event == EVENT_PRESS_D:
                                eo_timer.cancel()
                                return STATE_WAIT_FOR_VESSEL     #Change to STATE_WAIT_FOR_VESSEL
            elif event == EVENT_PRESS_AST:
                                return STATE_INPUT
            else:
                                eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_WAIT_FOR_VESSEL:
            if event == EVENT_ENTERING_OUTER:
                                time.sleep(1)
                                pump.on()
                                flowPin.on()
                                eo_timer.start(FLOW_TIME_INC//2)
                                return STATE_FILLING
            elif event == EVENT_ENTERING_INNER:
                                return STATE_WAIT_FOR_VESSEL
            elif event == EVENT_PRESS_D:  #Key on Keypad tends to accept multiple inputs if there is no delay
                                return STATE_WAIT_FOR_VESSEL
            elif event == EVENT_PRESS_AST: #Just in case asterisk is somehow triggered
                                return STATE_WAIT_FOR_VESSEL
            else:
                                eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_FILLING:
            if event == EVENT_SCAN_TIMER:
                                count = 0
                                time.sleep_ms(FLOW_TIME_INC//2)
                                # Calculates waterflow within the past .25 seconds from time.sleep
                                flowRate = (count * 2.25)
                                flowTime += FLOW_TIME_INC
                                totalFlow += flowRate
                                totalFlowoz = totalFlow/29.574
                                print("flowRate is {:.3f} ml/s Time elasped is {:.2f} Total flow is {:.3f} oz".format(flowRate, flowTime, totalFlowoz))
                                if(totalFlowoz >= finalvalue):     #Stop dispensing water
                                    pump.off()
                                    flowPin.off()
                  
                                eo_timer.start(FLOW_TIME_INC//2)
                                return STATE_FILLING
            if event == EVENT_EXITING_OUTER:
                                #Turn off Pump
                                pump.off()
                                flowPin.off()
                                flowTime = 0
                                totalFlow = 0
                                valuelist.clear()
                                finalvalue = 0
                                lcd.clear()
                                disp_welcome()
                                speaker.freq(ENTER_NOTE)     #Double Beep
                                speaker.duty_u16(PWM_MAX//2)
                                time.sleep(0.0625)
                                speaker.duty_u16(0)
                                time.sleep(0.0625)
                                speaker.duty_u16(PWM_MAX//2)
                                time.sleep(0.125)
                                speaker.duty_u16(0)
                                wake_time = time.ticks_ms()


                                return STATE_SLEEP
            else:
                                eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)



#Initial Cond
keypad_init()
disp_welcome()
eo_timer.start(SCAN_MSECS)



#Main Function
eventer.loop(event_process, STATE_SLEEP)
