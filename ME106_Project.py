#ME106 FINAL PROJECT
#BY NICHOLAS LEE


import time
from machine import Pin, I2C, PWM

from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

USE_POLLING_EVENTER = False

DEBUG = True  # currently just for tracing state transitions

if USE_POLLING_EVENTER:
    from eventer_1b1t_polls import Event, Eventer
else:
    from eventer_keypad   import Event, Eventer

#Relative timers for autosleep and scanning keypad-inputs
SLEEP_TIME_MSECS = 5000
SCAN_MSECS = 250

# States of the state machine
STATE_SLEEP                 = 0
STATE_INPUT                 = 1
STATE_WAIT_FOR_VESSEL       = 2
STATE_FILLING               = 3
STATE_STR = ('STATE_SLEEP', 'STATE_INPUT', 'STATE_WAIT_FOR_VESSEL', 'STATE_FILLING')


# Consolidate error reporting methods (crash, print, beep, etc.) here
def error(err_string):
    raise Exception(err_string)

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
rows = [2, 3, 4, 5]
cols = [6, 7, 8, 9]

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

#When 'Enter' button is pushed, display confirmation on LCD screen
def disp_input(finalval):
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
#
#



'''
    FLOWMETER RELATED CODE
'''
#
#



'''
    USON RELATED CODE
'''
#
#



# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in the state machine.
def event_process(state, event):
    global wake_time
    if state == STATE_SLEEP:
            if event == Event.TIMER:
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
                eventer.timer_set(SCAN_MSECS, periodic=False)
                return STATE_SLEEP
            elif event == Event.PRESS_AST:
                speaker.freq(ENTER_NOTE)
                speaker.duty_u16(PWM_MAX//2)
                lcd.backlight_on()
                lcd.clear()
                lcd.putstr("Enter Amount")
                lcd.move_to(0,1)
                lcd.blink_cursor_on()
                return STATE_INPUT
            elif event == Event.PRESS_D:
                return STATE_SLEEP
            else:
                error("Unrecognized event "+str(event)+" in STATE_SLEEP")
    elif state == STATE_INPUT:
            if event == Event.TIMER:
                speaker.duty_u16(0)
                for row in range(4):
                    for col in range(4):
                        key = scan(row, col)
                        if key == KEY_DOWN:
                            #print('Key Pressed:', keys[row][col])
                            last_key = keys[row][col]
                            if last_key == "#":
                                valuelist.clear()
                                lcd.move_to(0,1)
                                lcd.putstr("  ")
                                lcd.move_to(0,1)
                                speaker.freq(BUTTON_NOTE)
                                speaker.duty_u16(PWM_MAX//2)
                            elif last_key == "*":     #We do not want this as an input
                                pass
                            elif last_key == "A":     #Press A for 8oz Preset
                                finalvalue = 8
                                disp_input(finalvalue)
                            elif last_key == "B":     #Press B for 16oz Preset
                                finalvalue = 16
                                disp_input(finalvalue)
                            elif last_key == "C":     #Press C for 32oz Preset
                                finalvalue = 32
                                disp_input(finalvalue)
                            elif last_key == "D":     #Press D as Enter Key
                                if valuelist == []:   #If no input, Set D to 64oz Preset 
                                    finalvalue = 64
                                    disp_input(finalvalue)
                                else:
                                    finalvalue = int(''.join(valuelist))     #Confirm Input
                                    if finalvalue >= 64:     #Max limit is 64oz
                                        finalvalue = 64
                                        disp_limit(finalvalue)
                                    else:    
                                        disp_input(finalvalue)
                            elif len(valuelist) >= 2:
                                print('Digit Limit Reached')
                                speaker.freq(ERROR_NOTE)
                                speaker.duty_u16(PWM_MAX//2)
                                time.sleep(0.0625)
                                speaker.duty_u16(0)
                                time.sleep(0.0625)
                                speaker.duty_u16(PWM_MAX//2)    #Buzzer plays double beep to inform user of error
                            else:
                                valuelist.append(last_key)     #Add inputted digit to list of values to later convert to value
                                lcd.putstr(last_key)
                                speaker.freq(BUTTON_NOTE)
                                speaker.duty_u16(PWM_MAX//2)
                eventer.timer_set(SCAN_MSECS, periodic=False)
                return STATE_INPUT
            elif event == Event.PRESS_D:
                eventer.timer_cancel()
                return STATE_WAIT_FOR_VESSEL
            elif event == Event.PRESS_AST:
                return STATE_INPUT
            else:
                error("Unrecognized event in STATE_INPUT")
    elif state == STATE_WAIT_FOR_VESSEL:
            if event == Event.PRESS_D:  #Key on Keypad tends to accept multiple inputs if there is no delay
                return STATE_WAIT_FOR_VESSEL
            if event == Event.PRESS_AST: #Just in case asterisk is somehow triggered
                return STATE_WAIT_FOR_VESSEL
            
### INSERT RANGEFINDER CODE HERE! ###
            
            else:
                error("Unrecognized event in STATE_WAIT_FOR_VESSEL")
    else:
            error("Unrecognized state: "+str(state))
            
            

# INITIAL CONDITIONS SETUP
keypad_init()

lcd.putstr("Welcome!")
lcd.move_to(0,1)
lcd.putstr("Push * To Begin")

# NO CHANGES SHOULD NEED TO BE MADE BELOW THIS POINT
# unless you want to *temporarily* add some extra debugging code
#
# Keep checking for events and give them to the state machine
# to process (that is, perform the appropriate action for the
# current state and event, and advance to the next state).
# While Loop taken by Flashlight1+Blinking written by Eric Wertz
eventer = Eventer()
eventer.timer_set(SCAN_MSECS, periodic=False)
state = STATE_SLEEP
if DEBUG: print(STATE_STR[state])

while True:
    if USE_POLLING_EVENTER:
        eventer.update()

    event = eventer.next()
    if event != Event.NONE:
        if DEBUG: print(Event.to_string(event), end="")
        state_new = event_process(state, event)
        if DEBUG: print(" -> "+STATE_STR[state_new])
        state = state_new


