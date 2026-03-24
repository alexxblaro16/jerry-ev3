#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch

ev3 = EV3Brick()
motor_izquierdo = Motor(Port.D)
motor_derecho = Motor(Port.A)
robot = DriveBase(motor_izquierdo, motor_derecho, 55.5, 95)

sensor_izq    = ColorSensor(Port.S4)
sensor_centro = ColorSensor(Port.S3)
sensor_der    = ColorSensor(Port.S1)

VEL_RECTA  = 280
VEL_CURVA  = 110
VEL_90     = 55

GIRO_90      = 195
GIRO_RESCATE = 130

# Mismo PD que el original (funcionaba perfecto)
KP = 1.4
KD = 4.5

UMBRAL_NEGRO  = 25
UMBRAL_BLANCO = 60

TIEMPO_DIAMANTE_MS   = 220
COOLDOWN_DIAMANTE_MS = 150
COOLDOWN_CURVA_MS    = 100
IMPULSO_CURVA_MS     = 60
VEL_RETRO_RESCATE    = -80
TIEMPO_RETRO_RESCATE = 100

# Aceleración moderada para transiciones suaves
robot.settings(straight_speed=VEL_RECTA, straight_acceleration=600,
               turn_rate=GIRO_90, turn_acceleration=400)

error_previo        = 0
ultimo_error_valido = 0
en_diamante         = False
rescate_retroceso   = False
temporizador        = StopWatch()
cooldown_timer      = StopWatch()
cooldown_duracion   = 0

def zona(val):
    if val < UMBRAL_NEGRO:
        return 0
    elif val > UMBRAL_BLANCO:
        return 2
    else:
        return 1

# ==========================================
# PANTALLA INICIO
# ==========================================
ev3.light.on(Color.ORANGE)
ev3.screen.clear()
ev3.screen.print("  SIGUELINEAS  ")
ev3.screen.print("  Pulsa CENTER ")
ev3.screen.print("  para iniciar ")
ev3.screen.print("       :)      ")

while Button.CENTER not in ev3.buttons.pressed():
    wait(10)
wait(300)  # antirrebote

ev3.speaker.beep()
ev3.screen.clear()
ev3.screen.print("   CORRIENDO   ")
ev3.screen.print("  CENTER para  ")
ev3.screen.print("    pausar     ")
ev3.light.on(Color.GREEN)
wait(500)

# ==========================================
# BUCLE PRINCIPAL
# ==========================================
while True:

    # --- COMPRUEBA PAUSA EN CADA CICLO ---
    if Button.CENTER in ev3.buttons.pressed():
        robot.stop()
        ev3.light.on(Color.ORANGE)
        ev3.screen.clear()
        ev3.screen.print("   PAUSADO     ")
        ev3.screen.print("  Pulsa CENTER ")
        ev3.screen.print("  para seguir  ")
        ev3.screen.print("       :)      ")

        wait(400)  # antirrebote
        while Button.CENTER not in ev3.buttons.pressed():
            wait(10)
        wait(300)  # antirrebote

        ev3.speaker.beep()
        ev3.screen.clear()
        ev3.screen.print("   CORRIENDO   ")
        ev3.screen.print("  CENTER para  ")
        ev3.screen.print("    pausar     ")
        ev3.light.on(Color.GREEN)
        error_previo = 0
        wait(200)

    l_izq = sensor_izq.reflection()
    l_cen = sensor_centro.reflection()
    l_der = sensor_der.reflection()

    iz = zona(l_izq)
    ce = zona(l_cen)
    de = zona(l_der)

    en_cooldown = cooldown_timer.time() < cooldown_duracion

    # Resetear flag de retroceso cuando ya no estamos en rescate
    if not (iz == 2 and ce == 2 and de == 2):
        rescate_retroceso = False

    # --------------------------------------------------
    # CASO 1: DIAMANTE
    # --------------------------------------------------
    if iz == 0 and ce == 0 and de == 0 and not en_diamante and not en_cooldown:
        ev3.light.on(Color.RED)
        en_diamante = True
        temporizador.reset()

        while temporizador.time() < TIEMPO_DIAMANTE_MS:
            robot.drive(VEL_RECTA, 0)
            wait(5)

        robot.drive(VEL_CURVA, 0)
        wait(80)

        en_diamante = False
        cooldown_timer.reset()
        cooldown_duracion = COOLDOWN_DIAMANTE_MS
        error_previo = 0
        continue

    # --------------------------------------------------
    # CASO 2: RESCATE
    # --------------------------------------------------
    if iz == 2 and ce == 2 and de == 2:
        ev3.light.on(Color.ORANGE)

        # Retroceder un poco antes de girar (solo la primera vez)
        if not rescate_retroceso:
            t = StopWatch()
            while t.time() < TIEMPO_RETRO_RESCATE:
                robot.drive(VEL_RETRO_RESCATE, 0)
                wait(5)
            robot.stop()
            rescate_retroceso = True

        if ultimo_error_valido >= 0:
            robot.drive(0, GIRO_RESCATE)
        else:
            robot.drive(0, -GIRO_RESCATE)
        wait(5)
        continue

    # --------------------------------------------------
    # CASO 3: CURVA 90° IZQUIERDA
    # --------------------------------------------------
    if iz == 0 and ce == 2 and de == 2 and not en_cooldown:
        ev3.light.on(Color.YELLOW)

        # Impulso hacia adelante para desplazar centro de giro a la esquina
        t = StopWatch()
        while t.time() < IMPULSO_CURVA_MS:
            robot.drive(VEL_CURVA, 0)
            wait(5)

        t = StopWatch()
        while t.time() < 2500:
            robot.drive(VEL_90, -GIRO_90)
            wait(5)
            if zona(sensor_centro.reflection()) == 0:
                break

        robot.stop()
        wait(30)
        ultimo_error_valido = -1
        error_previo = 0
        cooldown_timer.reset()
        cooldown_duracion = COOLDOWN_CURVA_MS
        continue

    # --------------------------------------------------
    # CASO 4: CURVA 90° DERECHA
    # --------------------------------------------------
    if de == 0 and ce == 2 and iz == 2 and not en_cooldown:
        ev3.light.on(Color.YELLOW)

        # Impulso hacia adelante para desplazar centro de giro a la esquina
        t = StopWatch()
        while t.time() < IMPULSO_CURVA_MS:
            robot.drive(VEL_CURVA, 0)
            wait(5)

        t = StopWatch()
        while t.time() < 2500:
            robot.drive(VEL_90, GIRO_90)
            wait(5)
            if zona(sensor_centro.reflection()) == 0:
                break

        robot.stop()
        wait(30)
        ultimo_error_valido = 1
        error_previo = 0
        cooldown_timer.reset()
        cooldown_duracion = COOLDOWN_CURVA_MS
        continue

    # --------------------------------------------------
    # CASO 5: SIGUELÍNEAS PD (mismo que el original)
    # --------------------------------------------------
    ev3.light.on(Color.GREEN)

    error = l_izq - l_der

    if abs(error) > 5:
        ultimo_error_valido = error

    if ce == 0:
        velocidad = VEL_RECTA
        kp_actual = KP * 0.55
    elif ce == 1:
        velocidad = VEL_CURVA
        kp_actual = KP
    else:
        velocidad = VEL_CURVA * 0.75
        kp_actual = KP * 1.4

    derivada = error - error_previo
    giro = (error * kp_actual) + (derivada * KD)
    giro = max(-GIRO_90, min(GIRO_90, giro))

    robot.drive(velocidad, giro)
    error_previo = error
    wait(5)
