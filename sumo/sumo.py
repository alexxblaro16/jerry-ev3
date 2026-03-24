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
VEL_BUSQUEDA = 300
VEL_RETRO    = -600
VEL_AVANCE   = 800

UMBRAL_US    = 400
UMBRAL_NEGRO = 25

TIEMPO_RETRO_MS  = 200
TIEMPO_GIRO_MS   = 400
TIEMPO_AVANCE_MS = 200

ultimo_giro    = 1
temporizador   = StopWatch()
busqueda_timer = StopWatch()

def en_borde():
    """Comprueba si ALGÚN sensor toca borde negro"""
    return (sensor_izq.reflection() < UMBRAL_NEGRO or
            sensor_der.reflection() < UMBRAL_NEGRO or
            sensor_trasero.reflection() < UMBRAL_NEGRO)

def borde_frontal():
    return (sensor_izq.reflection() < UMBRAL_NEGRO or
            sensor_der.reflection() < UMBRAL_NEGRO)

def borde_trasero():
    return sensor_trasero.reflection() < UMBRAL_NEGRO

def escapar_borde():
    """Escapa del borde y vuelve al centro. SIEMPRE se ejecuta completo."""
    global ultimo_giro
    robot.stop()

    b_izq = sensor_izq.reflection() < UMBRAL_NEGRO
    b_der = sensor_der.reflection() < UMBRAL_NEGRO
    b_tras = sensor_trasero.reflection() < UMBRAL_NEGRO

    if b_tras:
        # Borde trasero: avanzar
        temporizador.reset()
        while temporizador.time() < TIEMPO_AVANCE_MS:
            robot.drive(VEL_AVANCE, 0)
            wait(2)
            # Si ahora toca borde frontal, parar
            if borde_frontal():
                break
        robot.stop()
    else:
        # Borde frontal: retroceder
        if b_izq and not b_der:
            giro = 200
            ultimo_giro = 1
        elif b_der and not b_izq:
            giro = -200
            ultimo_giro = -1
        else:
            giro = ultimo_giro * 200

        temporizador.reset()
        while temporizador.time() < TIEMPO_RETRO_MS:
            robot.drive(VEL_RETRO, 0)
            wait(2)
            # Si ahora toca borde trasero, parar
            if borde_trasero():
                break

        temporizador.reset()
        while temporizador.time() < TIEMPO_GIRO_MS:
            robot.drive(0, giro)
            wait(2)

    robot.stop()

# ==========================================
# PANTALLA INICIO
# ==========================================
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

# Cuenta atrás reglamentaria de 5 segundos
for i in range(3, 0, -1):
    ev3.screen.clear()
    ev3.screen.print("  CUENTA ATRAS ")
    ev3.screen.print("      " + str(i) + "        ")
    ev3.speaker.beep(frequency=600, duration=100)
    ev3.light.on(Color.ORANGE)
    wait(900)

ev3.speaker.beep(frequency=1000, duration=200)
ev3.screen.clear()
ev3.screen.print("  COMBATIENDO  ")
ev3.screen.print("  CENTER=pausa ")
ev3.light.on(Color.GREEN)

# ==========================================
# BUCLE PRINCIPAL
# ==========================================
while True:

    # --- PAUSA ---
    if Button.CENTER in ev3.buttons.pressed():
        robot.stop()
        ev3.light.on(Color.ORANGE)
        ev3.screen.clear()
        ev3.screen.print("   PAUSADO     ")
        ev3.screen.print("  CENTER=seguir")
        wait(400)
        while Button.CENTER not in ev3.buttons.pressed():
            wait(10)
        wait(300)
        ev3.screen.clear()
        ev3.screen.print("  COMBATIENDO  ")
        ev3.screen.print("  CENTER=pausa ")
        ev3.light.on(Color.GREEN)
        wait(200)

    # === PRIORIDAD ABSOLUTA: BORDE ===
    if en_borde():
        ev3.light.on(Color.RED)
        escapar_borde()
        continue

    # === RIVAL DETECTADO: ATACAR ===
    distancia = sensor_us.distance()

    if distancia < UMBRAL_US:
        ev3.light.on(Color.RED)
        busqueda_timer.reset()

        # Atacar mientras lo vea y no toque borde
        while sensor_us.distance() < UMBRAL_US:
            robot.drive(VEL_ATAQUE, 0)
            wait(2)

            # Si toca borde, escapar INMEDIATAMENTE
            if en_borde():
                escapar_borde()
                break
        continue

    # === BÚSQUEDA: girar buscando rival ===
    ev3.light.on(Color.YELLOW)

    # Girar en el sitio buscando al rival (más efectivo que ir recto)
    if busqueda_timer.time() < 1000:
        robot.drive(0, ultimo_giro * 200)
    else:
        # Avanzar un poco y volver a buscar girando
        robot.drive(VEL_BUSQUEDA, 0)
        if busqueda_timer.time() > 1500:
            ultimo_giro = -ultimo_giro
            busqueda_timer.reset()

    # Protección de borde incluso en búsqueda
    if en_borde():
        escapar_borde()

    wait(2)
