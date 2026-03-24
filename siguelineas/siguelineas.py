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

VEL_MAX    = 350   # Recta confirmada (centro negro + error bajo)
VEL_RECTA  = 200   # Centro en negro pero con algo de error
VEL_CURVA  = 100   # Centro en gris (entrando en curva)
VEL_90     = 65

GIRO_90      = 200
GIRO_RESCATE = 130

KP       = 1.4
KD_RECTA = 1.5    # Derivada suave en recta (no amplifica ruido)
KD_CURVA = 4.5    # Derivada fuerte en curva (reacción rápida)

UMBRAL_NEGRO  = 25
UMBRAL_BLANCO = 60
BANDA_MUERTA  = 8  # Error por debajo de esto en recta = ir recto sin corregir

TIEMPO_DIAMANTE_MS = 220
COOLDOWN_DIAMANTE_MS = 150
COOLDOWN_CURVA_MS    = 100

# Aceleración agresiva para transiciones rápidas entre velocidades
robot.settings(straight_speed=VEL_MAX, straight_acceleration=800,
               turn_rate=GIRO_90, turn_acceleration=600)

error_previo        = 0
ultimo_error_valido = 0
en_diamante         = False
temporizador        = StopWatch()
cooldown_timer      = StopWatch()
cooldown_duracion   = 0

# Historial para media móvil (3 muestras)
err_h0 = 0
err_h1 = 0
err_h2 = 0

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
ev3.screen.print("               ")
ev3.screen.print("  Pulsa CENTER ")
ev3.screen.print("  para iniciar ")
ev3.screen.print("       :)      ")

while Button.CENTER not in ev3.buttons.pressed():
    wait(10)
wait(300)  # antirrebote

ev3.speaker.beep()
ev3.screen.clear()
ev3.screen.print("   CORRIENDO   ")
ev3.screen.print("               ")
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
        ev3.screen.print("               ")
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
        ev3.screen.print("               ")
        ev3.screen.print("  CENTER para  ")
        ev3.screen.print("    pausar     ")
        ev3.light.on(Color.GREEN)
        wait(200)

    l_izq = sensor_izq.reflection()
    l_cen = sensor_centro.reflection()
    l_der = sensor_der.reflection()

    iz = zona(l_izq)
    ce = zona(l_cen)
    de = zona(l_der)

    en_cooldown = cooldown_timer.time() < cooldown_duracion

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
        err_h0 = err_h1 = err_h2 = 0
        continue

    # --------------------------------------------------
    # CASO 2: RESCATE
    # --------------------------------------------------
    if iz == 2 and ce == 2 and de == 2:
        ev3.light.on(Color.ORANGE)
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
        robot.stop()
        wait(30)

        t = StopWatch()
        while t.time() < 2500:
            robot.drive(VEL_90, -GIRO_90)
            wait(5)
            if zona(sensor_centro.reflection()) == 0:
                break

        robot.stop()
        wait(20)
        ultimo_error_valido = -1
        error_previo = 0
        err_h0 = err_h1 = err_h2 = 0
        cooldown_timer.reset()
        cooldown_duracion = COOLDOWN_CURVA_MS
        continue

    # --------------------------------------------------
    # CASO 4: CURVA 90° DERECHA
    # --------------------------------------------------
    if de == 0 and ce == 2 and iz == 2 and not en_cooldown:
        ev3.light.on(Color.YELLOW)
        robot.stop()
        wait(30)

        t = StopWatch()
        while t.time() < 2500:
            robot.drive(VEL_90, GIRO_90)
            wait(5)
            if zona(sensor_centro.reflection()) == 0:
                break

        robot.stop()
        wait(20)
        ultimo_error_valido = 1
        error_previo = 0
        err_h0 = err_h1 = err_h2 = 0
        cooldown_timer.reset()
        cooldown_duracion = COOLDOWN_CURVA_MS
        continue

    # --------------------------------------------------
    # CASO 5: SIGUELÍNEAS PD
    # --------------------------------------------------
    ev3.light.on(Color.GREEN)

    error_crudo = l_izq - l_der

    # Media móvil de 3 muestras para suavizar ruido
    err_h2 = err_h1
    err_h1 = err_h0
    err_h0 = error_crudo
    error = (err_h0 + err_h1 + err_h2) // 3

    if abs(error) > 5:
        ultimo_error_valido = error

    # Recta confirmada: centro negro + laterales blancos + error bajo
    recta_confirmada = (ce == 0 and iz == 2 and de == 2 and abs(error) < BANDA_MUERTA)

    if recta_confirmada:
        # Banda muerta: ir recto a máxima velocidad sin correcciones
        robot.drive(VEL_MAX, 0)
        error_previo = 0
    else:
        # Velocidad continua: menos error = más rápido
        error_abs = abs(error)
        if ce == 0:
            # Centro en negro: velocidad proporcional entre VEL_RECTA y VEL_MAX
            factor = max(0, 1 - error_abs / 40)
            velocidad = VEL_CURVA + int((VEL_RECTA - VEL_CURVA) * factor)
            kp_actual = KP * 0.55
            kd_actual = KD_RECTA
        elif ce == 1:
            # Centro en gris: velocidad proporcional entre VEL_CURVA*0.75 y VEL_CURVA
            factor = max(0, 1 - error_abs / 50)
            velocidad = int(VEL_CURVA * 0.75) + int((VEL_CURVA - VEL_CURVA * 0.75) * factor)
            kp_actual = KP
            kd_actual = KD_CURVA
        else:
            # Centro en blanco: velocidad mínima, máxima corrección
            velocidad = int(VEL_CURVA * 0.6)
            kp_actual = KP * 1.4
            kd_actual = KD_CURVA

        derivada = error - error_previo
        giro = (error * kp_actual) + (derivada * kd_actual)
        giro = max(-GIRO_90, min(GIRO_90, giro))

        robot.drive(velocidad, giro)
        error_previo = error

    wait(2)