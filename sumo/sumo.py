#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor, UltrasonicSensor
from pybricks.parameters import Port, Color, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch

ev3 = EV3Brick()
motor_izquierdo = Motor(Port.D)
motor_derecho = Motor(Port.A)
robot = DriveBase(motor_izquierdo, motor_derecho, 55.5, 95)
robot.settings(straight_speed=1000, straight_acceleration=1500,
               turn_rate=300, turn_acceleration=1200)

sensor_izq     = ColorSensor(Port.S4)
sensor_der     = ColorSensor(Port.S1)
sensor_us      = UltrasonicSensor(Port.S2)
sensor_trasero = ColorSensor(Port.S3)

VEL_ATAQUE   = 1000
VEL_BUSQUEDA = 400
VEL_RETRO    = -500
VEL_AVANCE   = 600

UMBRAL_US    = 400   # Rival a 122mm, sin nada 660mm → 400 perfecto
UMBRAL_NEGRO = 25

TIEMPO_RETRO_MS  = 300
TIEMPO_GIRO_MS   = 600
TIEMPO_AVANCE_MS = 400

ultimo_giro  = 1
temporizador = StopWatch()

def borde_izq():
    return sensor_izq.reflection() < UMBRAL_NEGRO

def borde_der():
    return sensor_der.reflection() < UMBRAL_NEGRO

def borde_trasero():
    return sensor_trasero.reflection() < UMBRAL_NEGRO

def borde_frontal():
    return borde_izq() or borde_der()

ev3.light.on(Color.ORANGE)
ev3.screen.clear()
ev3.screen.print("    SUMO EV3   ")
ev3.screen.print("               ")
ev3.screen.print("  Pulsa CENTER ")
ev3.screen.print("  para iniciar ")
ev3.screen.print("       :)      ")

while Button.CENTER not in ev3.buttons.pressed():
    wait(10)
wait(300)

ev3.speaker.beep(frequency=800, duration=100)
ev3.screen.clear()
ev3.screen.print("  COMBATIENDO  ")
ev3.screen.print("               ")
ev3.screen.print("  CENTER para  ")
ev3.screen.print("    pausar     ")
ev3.light.on(Color.GREEN)
wait(500)

while True:

    if Button.CENTER in ev3.buttons.pressed():
        robot.stop()
        ev3.light.on(Color.ORANGE)
        ev3.speaker.beep(frequency=400, duration=200)
        ev3.screen.clear()
        ev3.screen.print("   PAUSADO     ")
        ev3.screen.print("               ")
        ev3.screen.print("  Pulsa CENTER ")
        ev3.screen.print("  para seguir  ")
        ev3.screen.print("       :)      ")
        wait(400)
        while Button.CENTER not in ev3.buttons.pressed():
            wait(10)
        wait(300)
        ev3.speaker.beep(frequency=800, duration=100)
        ev3.screen.clear()
        ev3.screen.print("  COMBATIENDO  ")
        ev3.screen.print("               ")
        ev3.screen.print("  CENTER para  ")
        ev3.screen.print("    pausar     ")
        ev3.light.on(Color.GREEN)
        wait(200)

    distancia = sensor_us.distance()

    # Cachear lecturas de borde (evita releer sensores múltiples veces)
    b_izq = sensor_izq.reflection() < UMBRAL_NEGRO
    b_der = sensor_der.reflection() < UMBRAL_NEGRO
    b_tras = sensor_trasero.reflection() < UMBRAL_NEGRO

    # PRIORIDAD 1A: BORDE TRASERO
    if b_tras:
        ev3.light.on(Color.RED)
        temporizador.reset()
        while temporizador.time() < TIEMPO_AVANCE_MS:
            robot.drive(VEL_AVANCE, 0)
            wait(2)
            if sensor_trasero.reflection() >= UMBRAL_NEGRO:
                break
        continue

    # PRIORIDAD 1B: BORDE FRONTAL
    if b_izq or b_der:
        ev3.light.on(Color.RED)

        if b_izq and not b_der:
            giro_escape = 200
            ultimo_giro = 1
        elif b_der and not b_izq:
            giro_escape = -200
            ultimo_giro = -1
        else:
            giro_escape = ultimo_giro * 200

        temporizador.reset()
        while temporizador.time() < TIEMPO_RETRO_MS:
            robot.drive(VEL_RETRO, 0)
            wait(2)

        temporizador.reset()
        while temporizador.time() < TIEMPO_GIRO_MS:
            robot.drive(0, giro_escape)
            wait(2)

        continue

    # PRIORIDAD 2: RIVAL DETECTADO
    if distancia < UMBRAL_US:
        ev3.light.on(Color.RED)
        robot.drive(VEL_ATAQUE, 0)
        wait(2)
        continue

    # PRIORIDAD 3: BÚSQUEDA
    ev3.light.on(Color.YELLOW)
    robot.drive(VEL_BUSQUEDA, 0)
    wait(2)