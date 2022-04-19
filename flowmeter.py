#!/usr/bin/python
#flowsensor.py
from machine import Pin
import time
global flowTime
global totalFlow

FLOW_PIN = const(15)
FLOW_TIME_INC = 0.25

flowPin = Pin(FLOW_PIN, Pin.IN)
flowPin.on()

flowTime = 0
totalFlow = 0
def flow(pin):
    global count
    count += 1


flowPin.irq(trigger=Pin.IRQ_RISING, handler=flow)

while True:
    count = 0
    time.sleep(FLOW_TIME_INC)
    # Calculates waterflow within the past .25 seconds from time.sleep
    flowRate = (count * 2.25)
    flowTime += FLOW_TIME_INC
    #instantFlow = flowRate * FLOW_TIME_INC
    totalFlow += flowRate
    print("flowRate is {:.3f} ml/s Time elasped is {:.2f} Total flow is {:.3f} mL".format(flowRate, flowTime, instantFlow, totalFlow))