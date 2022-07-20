# ME106FinalProject

SJSU ME106 Fundamentals of Mechatronics Final Project by Nicholas Lee, Michael Korens, and Raaed Annan

[Project Link](https://express.adobe.com/page/mOr6UGISbOYoW/)

Aim of the project is to create an autonomous smart water dispenser that detects the presence of a vessel and fills it up to a user-specified amount.

The project uses the following components to achieve this:

* Raspberry Pi Pico Microcontroller
* 4 x 4 Matrix Array Membrane Keypad
* HD44780 IIC I2C1602 LCD Display
* HC-SR04 Ultrasonic Sensor
* N-Channel MOSFET 60V 30A
* 12V Brushless DC Pump
* Volumetric Hall Effect Flow Sensor
* 12V 2A Power Supply
* Adjustable Voltage Buck Converter
* Voltage Logic Level Shifter

The project follows a State Machine Structure modified from a state machine template provided by Eric Wertz.
In order to utilize the state machine, respective eventer and eventoid libraries must be downloaded.

The following is a State machine diagram that showcases the different states and events that switch between the states in the program:

![State Machine Diagram](/StateDiagram.png)
