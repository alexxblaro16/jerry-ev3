#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import ColorSensor
from pybricks.parameters import Port
from pybricks.tools import wait

ev3 = EV3Brick()
s1 = ColorSensor(Port.S1)
s3 = ColorSensor(Port.S3)
s4 = ColorSensor(Port.S4)

while True:
    ev3.screen.clear()
    ev3.screen.print("S1 der: " + str(s1.reflection()))
    ev3.screen.print("S3 cent:" + str(s3.reflection()))
    ev3.screen.print("S4 izq: " + str(s4.reflection()))
    wait(300)