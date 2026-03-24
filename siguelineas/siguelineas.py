#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Color, Button, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch

ev3 = EV3Brick()
motor_izq = Motor(Port.D)
motor_der = Motor(Port.A)
robot = DriveBase(motor_izq, motor_der, 55.5, 95)

sensor_izq    = ColorSensor(Port.S4)
sensor_centro = ColorSensor(Port.S3)
sensor_der    = ColorSensor(Port.S1)

# ==========================================
# CONSTANTES
# ==========================================
VEL_RECTA  = 400
VEL_CURVA  = 140
VEL_90     = 60

GIRO_90      = 200
GIRO_RESCATE = 130

KP = 1.4
KD = 4.5

UMBRAL_NEGRO  = 25
UMBRAL_BLANCO = 60

TIEMPO_DIAMANTE_MS = 220

# Conversion mm/s a deg/s para control directo de motores
# Rueda 55.5mm diametro → circunferencia = pi * 55.5 ≈ 174.4mm
# 1 mm/s ≈ 2.065 deg/s
MM_A_DEG = 2.065

robot.settings(straight_speed=VEL_RECTA, straight_acceleration=900,
               turn_rate=GIRO_90, turn_acceleration=600)

# ==========================================
# VARIABLES DE ESTADO
# ==========================================
error_previo        = 0
ultimo_error_valido = 0
en_diamante         = False
cooldown            = 0
temporizador        = StopWatch()
estrategia          = 0   # 0=parado, 1=PD, 2=laberinto, 3=pivot, 4=sonda

# Para estrategia sonda
sonda_dir = 1

NOMBRES_ESTRATEGIA = [
    "   PARADO     ",
    " 1: PD NORMAL ",
    " 2: LABERINTO ",
    " 3: PIVOT     ",
    " 4: SONDA     ",
]

COLORES_ESTRATEGIA = [
    Color.ORANGE,
    Color.GREEN,
    Color.YELLOW,
    Color.RED,
    Color.ORANGE,
]

def zona(val):
    if val < UMBRAL_NEGRO:
        return 0
    elif val > UMBRAL_BLANCO:
        return 2
    else:
        return 1

def mostrar_estrategia():
    ev3.screen.clear()
    ev3.screen.print("  SIGUELINEAS  ")
    ev3.screen.print(NOMBRES_ESTRATEGIA[estrategia])
    if estrategia == 0:
        ev3.screen.print(" CENTER: start ")
    else:
        ev3.screen.print(" CENTER: next  ")
    ev3.light.on(COLORES_ESTRATEGIA[estrategia])

def reset_estado():
    global error_previo, ultimo_error_valido, en_diamante, cooldown, sonda_dir
    error_previo = 0
    ultimo_error_valido = 0
    en_diamante = False
    cooldown = 0
    sonda_dir = 1
    robot.stop()
    motor_izq.stop()
    motor_der.stop()

# ==========================================
# PANTALLA INICIO
# ==========================================
mostrar_estrategia()

while Button.CENTER not in ev3.buttons.pressed():
    wait(10)
wait(400)

# ==========================================
# BUCLE PRINCIPAL
# ==========================================
while True:

    # --- COMPRUEBA BOTÓN CENTER PARA CAMBIAR ESTRATEGIA ---
    if Button.CENTER in ev3.buttons.pressed():
        reset_estado()
        estrategia = (estrategia + 1) % 5
        ev3.speaker.beep()
        mostrar_estrategia()
        wait(500)
        continue

    # Si está parado, no hacer nada
    if estrategia == 0:
        wait(10)
        continue

    # --- LECTURA DE SENSORES ---
    l_izq = sensor_izq.reflection()
    l_cen = sensor_centro.reflection()
    l_der = sensor_der.reflection()

    iz = zona(l_izq)
    ce = zona(l_cen)
    de = zona(l_der)

    if cooldown > 0:
        cooldown -= 1

    # ==========================================================
    # ESTRATEGIA 1: PD NORMAL (la que ya funcionaba)
    # ==========================================================
    if estrategia == 1:

        # DIAMANTE
        if iz == 0 and ce == 0 and de == 0 and not en_diamante and cooldown == 0:
            ev3.light.on(Color.RED)
            en_diamante = True
            temporizador.reset()

            while temporizador.time() < TIEMPO_DIAMANTE_MS:
                robot.drive(VEL_RECTA, 0)
                wait(5)

            robot.drive(VEL_CURVA, 40)
            wait(120)

            en_diamante = False
            cooldown = 30
            error_previo = 0
            ultimo_error_valido = 1
            continue

        # RESCATE
        if iz == 2 and ce == 2 and de == 2:
            ev3.light.on(Color.ORANGE)
            if ultimo_error_valido >= 0:
                robot.drive(0, GIRO_RESCATE)
            else:
                robot.drive(0, -GIRO_RESCATE)
            wait(5)
            continue

        # CURVA 90° IZQUIERDA
        if iz == 0 and ce == 2 and de == 2 and cooldown == 0:
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
            cooldown = 20
            continue

        # CURVA 90° DERECHA
        if de == 0 and ce == 2 and iz == 2 and cooldown == 0:
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
            cooldown = 20
            continue

        # SIGUELÍNEAS PD
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

        if ce == 0 and abs(error) < 6:
            giro = 0

        robot.drive(velocidad, giro)
        error_previo = error
        wait(5)

    # ==========================================================
    # ESTRATEGIA 2: LABERINTO (mano derecha)
    # ==========================================================
    elif estrategia == 2:

        # Sigue el borde derecho de la línea
        # Usa sensor derecho como referencia: intenta mantenerlo en la zona gris
        objetivo = 42  # Valor medio entre negro (25) y blanco (60)
        error = l_der - objetivo

        # DIAMANTE: avanzar recto y buscar línea a la derecha
        if iz == 0 and ce == 0 and de == 0 and cooldown == 0:
            ev3.light.on(Color.RED)
            temporizador.reset()
            while temporizador.time() < TIEMPO_DIAMANTE_MS:
                robot.drive(VEL_RECTA, 0)
                wait(5)
            robot.drive(VEL_CURVA, 40)
            wait(120)
            cooldown = 30
            continue

        # Perdido: girar a la derecha buscando la línea
        if iz == 2 and ce == 2 and de == 2:
            ev3.light.on(Color.ORANGE)
            robot.drive(VEL_CURVA // 2, 100)
            wait(5)
            continue

        # PD sobre el borde derecho
        ev3.light.on(Color.YELLOW)
        giro = error * 2.0
        giro = max(-GIRO_90, min(GIRO_90, giro))

        if de == 0:
            velocidad = VEL_RECTA
        elif de == 1:
            velocidad = VEL_CURVA
        else:
            velocidad = VEL_CURVA // 2

        robot.drive(velocidad, giro)
        wait(5)

    # ==========================================================
    # ESTRATEGIA 3: PIVOT (punto de apoyo)
    # ==========================================================
    elif estrategia == 3:

        # Mismo PD que estrategia 1 pero gira sobre una rueda fija

        # DIAMANTE
        if iz == 0 and ce == 0 and de == 0 and not en_diamante and cooldown == 0:
            ev3.light.on(Color.RED)
            en_diamante = True
            temporizador.reset()
            vel_deg = int(VEL_RECTA * MM_A_DEG)
            while temporizador.time() < TIEMPO_DIAMANTE_MS:
                motor_izq.run(vel_deg)
                motor_der.run(vel_deg)
                wait(5)
            motor_izq.run(int(VEL_CURVA * MM_A_DEG))
            motor_der.run(int(VEL_CURVA * MM_A_DEG * 0.7))
            wait(120)
            motor_izq.stop()
            motor_der.stop()
            en_diamante = False
            cooldown = 30
            error_previo = 0
            ultimo_error_valido = 1
            continue

        # RESCATE
        if iz == 2 and ce == 2 and de == 2:
            ev3.light.on(Color.ORANGE)
            vel_giro = int(GIRO_RESCATE * MM_A_DEG)
            if ultimo_error_valido >= 0:
                motor_izq.run(vel_giro)
                motor_der.hold()
            else:
                motor_izq.hold()
                motor_der.run(vel_giro)
            wait(5)
            continue

        # CURVA 90° IZQUIERDA (pivota sobre rueda izquierda)
        if iz == 0 and ce == 2 and de == 2 and cooldown == 0:
            ev3.light.on(Color.YELLOW)
            motor_izq.stop()
            motor_der.stop()
            wait(30)

            t = StopWatch()
            vel_giro = int(VEL_90 * MM_A_DEG * 2)
            while t.time() < 2500:
                motor_izq.hold()
                motor_der.run(-vel_giro)
                wait(5)
                if zona(sensor_centro.reflection()) == 0:
                    break

            motor_izq.stop()
            motor_der.stop()
            wait(20)
            ultimo_error_valido = -1
            error_previo = 0
            cooldown = 20
            continue

        # CURVA 90° DERECHA (pivota sobre rueda derecha)
        if de == 0 and ce == 2 and iz == 2 and cooldown == 0:
            ev3.light.on(Color.YELLOW)
            motor_izq.stop()
            motor_der.stop()
            wait(30)

            t = StopWatch()
            vel_giro = int(VEL_90 * MM_A_DEG * 2)
            while t.time() < 2500:
                motor_der.hold()
                motor_izq.run(vel_giro)
                wait(5)
                if zona(sensor_centro.reflection()) == 0:
                    break

            motor_izq.stop()
            motor_der.stop()
            wait(20)
            ultimo_error_valido = 1
            error_previo = 0
            cooldown = 20
            continue

        # SIGUELÍNEAS PD CON PIVOT
        ev3.light.on(Color.RED)
        error = l_izq - l_der

        if abs(error) > 5:
            ultimo_error_valido = error

        if ce == 0:
            kp_actual = KP * 0.55
        elif ce == 1:
            kp_actual = KP
        else:
            kp_actual = KP * 1.4

        derivada = error - error_previo
        correccion = (error * kp_actual) + (derivada * KD)

        vel_base = int(VEL_RECTA * MM_A_DEG) if ce == 0 else int(VEL_CURVA * MM_A_DEG)

        if ce == 0 and abs(error) < 6:
            # Recto sin corrección
            motor_izq.run(vel_base)
            motor_der.run(vel_base)
        elif correccion > 0:
            # Girar a la derecha: pivota sobre rueda derecha
            motor_der.hold()
            motor_izq.run(vel_base)
        elif correccion < 0:
            # Girar a la izquierda: pivota sobre rueda izquierda
            motor_izq.hold()
            motor_der.run(vel_base)
        else:
            motor_izq.run(vel_base)
            motor_der.run(vel_base)

        error_previo = error
        wait(5)

    # ==========================================================
    # ESTRATEGIA 4: SONDA (movimiento fluido sinusoidal)
    # ==========================================================
    elif estrategia == 4:

        ev3.light.on(Color.ORANGE)

        # Movimiento fluido: siempre avanza, oscila sobre la línea
        # Cuando cruza la línea (sensor opuesto la detecta), cambia dirección

        # Si el sensor del lado al que vamos detecta negro, cambiar dirección
        if sonda_dir == 1 and de == 0:
            sonda_dir = -1
        elif sonda_dir == -1 and iz == 0:
            sonda_dir = 1

        # Diamante: seguir recto
        if iz == 0 and ce == 0 and de == 0:
            robot.drive(VEL_RECTA, 0)
            wait(5)
            continue

        # Perdido: girar hacia último lado conocido
        if iz == 2 and ce == 2 and de == 2:
            robot.drive(VEL_CURVA // 2, sonda_dir * GIRO_RESCATE)
            wait(5)
            continue

        # Movimiento sinusoidal constante
        giro_sonda = sonda_dir * 60

        # Si el centro ve la línea, ir más rápido
        if ce == 0:
            robot.drive(VEL_RECTA, giro_sonda)
        else:
            robot.drive(VEL_CURVA, giro_sonda)

        wait(5)
