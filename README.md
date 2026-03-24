# Jerry — Robot EV3 Lego

Jerry es un robot construido con LEGO EV3 para la asignatura **Taller I** en UDIT. Cuenta con tres modos de operación independientes: siguelineas, sumo y control remoto por mando.

## Modos de operación

### Siguelineas
Programa de seguimiento de línea con control **PD (Proporcional-Derivativo)** usando 3 sensores de color en línea. Capaz de:
- Seguir líneas negras sobre fondo blanco a velocidad variable
- Detectar y atravesar **diamantes** (cruces donde los 3 sensores leen negro)
- Negociar **curvas de 90°** a izquierda y derecha
- **Rescate** automático cuando pierde la línea (3 sensores en blanco)
- Pausa y reanudación con el botón CENTER

### Sumo
Programa de combate en ring de sumo con sistema de prioridades:
1. **Borde trasero** → avanzar (te están empujando fuera)
2. **Borde frontal** → retroceder y girar (evitar caer)
3. **Rival detectado** → embestir a máxima velocidad
4. **Sin detección** → búsqueda avanzando recto

Usa 3 sensores de color (izquierdo, derecho y trasero) para detectar bordes y un sensor ultrasónico para localizar al rival.

### Mando RC
Servidor web embebido en el EV3 que sirve una interfaz de control remoto al navegador del móvil. Permite conducir el robot desde cualquier dispositivo conectado a la misma red. Soporta multi-touch para movimientos diagonales (avanzar + girar simultáneamente).

## Hardware

| Componente | Puerto |
|---|---|
| Motor izquierdo | D |
| Motor derecho | A |
| Sensor color izquierdo | S4 |
| Sensor color centro | S3 |
| Sensor color derecho | S1 |
| Sensor ultrasónico | S2 |

- Diámetro de rueda: 55.5 mm
- Distancia entre ejes: 95 mm

## Estructura del proyecto

```
jerry/
├── siguelineas/
│   ├── siguelineas.py      # Programa principal siguelineas
│   └── sensorescolor.py    # Utilidad de debug para sensores de color
├── sumo/
│   ├── sumo.py             # Programa principal sumo
│   └── ultrasonidos.py     # Utilidad de debug para sensor ultrasónico
├── mando/
│   └── mando_web.py        # Servidor web + interfaz de control remoto
└── README.md
```

## Requisitos

- LEGO EV3 Brick con firmware [ev3dev](https://www.ev3dev.org/) o compatible con pybricks
- [Pybricks MicroPython](https://pybricks.com/) instalado en el brick
- Para el mando: dispositivo con navegador web en la misma red que el EV3
