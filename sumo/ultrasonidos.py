#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import UltrasonicSensor
from pybricks.parameters import Port
from pybricks.tools import wait

ev3 = EV3Brick()
us = UltrasonicSensor(Port.S2)

while True:
    ev3.screen.clear()
    ev3.screen.print("US S2:")
    ev3.screen.print(str(us.distance()) + " mm")
    wait(300)