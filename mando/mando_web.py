#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait
import socket

ev3 = EV3Brick()

try:
    motor_izquierdo = Motor(Port.D)
    motor_derecho = Motor(Port.A)
    robot = DriveBase(motor_izquierdo, motor_derecho, 55.5, 95)

    # ==========================================
    # INTERFAZ WEB PRO (HORIZONTAL + NEÓN RC)
    # ==========================================
    HTML_UI = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, orientation=landscape">
<title>EV3 SUMO PRO</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; }

  body {
    background: #030305;
    background-image: 
      linear-gradient(rgba(0, 255, 204, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 255, 204, 0.03) 1px, transparent 1px);
    background-size: 30px 30px;
    color: #00ffcc;
    font-family: 'Orbitron', sans-serif;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  /* Aviso de rotación si está en vertical */
  #rotate-msg {
    display: none;
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: #000; z-index: 9999;
    flex-direction: column; align-items: center; justify-content: center;
    font-size: 24px; text-align: center; color: #00ffcc; text-shadow: 0 0 20px #00ffcc;
  }
  @media screen and (orientation: portrait) {
    #rotate-msg { display: flex; }
    .gamepad-container { display: none !important; }
  }

  .gamepad-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 100%;
    padding: 20px 60px;
  }

  /* Paneles de cristal lateral */
  .control-panel {
    display: flex;
    background: rgba(10, 15, 20, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 255, 204, 0.2);
    border-radius: 30px;
    padding: 30px;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(0, 255, 204, 0.05);
    gap: 20px;
  }

  .panel-left { flex-direction: column; }
  .panel-right { flex-direction: row; align-items: center; }

  /* Botones ciberpunk */
  .btn {
    width: 90px;
    height: 90px;
    background: linear-gradient(135deg, #071015, #0a1820);
    border: 2px solid #00ffcc44;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    color: #00ffcc88;
    box-shadow: 0 5px 15px rgba(0,0,0,0.5), inset 0 2px 5px rgba(255,255,255,0.05);
    transition: all 0.1s;
  }

  .btn.activo {
    background: #00ffcc;
    color: #000;
    border-color: #fff;
    box-shadow: 0 0 30px #00ffcc, 0 0 60px #00ffcc55, inset 0 0 10px rgba(255,255,255,0.8);
    transform: scale(0.9) translateY(4px);
  }

  /* HUD Central */
  .hud {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
  }

  .title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 6px;
    text-shadow: 0 0 15px #00ffcc;
    margin-bottom: 20px;
  }

  .radar {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    border: 2px dashed rgba(0, 255, 204, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 0 50px rgba(0,255,204,0.1);
  }

  .radar::after {
    content: ''; position: absolute; width: 100%; height: 100%;
    border-radius: 50%; border: 1px solid #00ffcc22;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0% { transform: scale(0.9); opacity: 1; }
    100% { transform: scale(1.4); opacity: 0; }
  }

  .robot-icon { font-size: 50px; filter: drop-shadow(0 0 10px #00ffcc); transition: 0.2s; }
  
  .status-text {
    margin-top: 25px;
    font-size: 14px;
    letter-spacing: 4px;
    color: #fff;
    background: rgba(0, 255, 204, 0.1);
    padding: 8px 20px;
    border-radius: 50px;
    border: 1px solid #00ffcc55;
  }

  .latency {
    position: absolute; bottom: 15px; font-size: 11px; letter-spacing: 2px; color: #00ffcc44;
  }
</style>
</head>
<body oncontextmenu="return false;">

<div id="rotate-msg">
  <div>🔄</div>
  <div>GIRA EL MÓVIL</div>
  <div style="font-size:12px; margin-top:10px; color:#666;">Modo Horizontal Requerido</div>
</div>

<div class="gamepad-container">
  
  <div class="control-panel panel-left">
    <div class="btn" id="W">⏫</div>
    <div class="btn" id="S">⏬</div>
  </div>

  <div class="hud">
    <div class="title">EV3 SUMO</div>
    <div class="radar">
      <div class="robot-icon" id="icon">🤖</div>
    </div>
    <div class="status-text" id="status">SISTEMA LISTO</div>
    <div class="latency">S25 ULTRA LINK | PING: 0ms</div>
  </div>

  <div class="control-panel panel-right">
    <div class="btn" id="A">⏪</div>
    <div class="btn" id="D">⏩</div>
  </div>

</div>

<script>
  const pulsadas = new Set();
  
  const descripciones = {
    W: 'AVANZANDO', S: 'RETROCEDIENDO', A: 'GIRANDO IZQ', D: 'GIRANDO DER',
    WA: 'CURVA IZQ', WD: 'CURVA DER', SA: 'MARCHA ATRÁS IZQ', SD: 'MARCHA ATRÁS DER', '': 'SISTEMA LISTO'
  };

  function updateUI() {
    const clave = ['W','S','A','D'].filter(k => pulsadas.has(k)).join('');
    document.getElementById('status').innerText = descripciones[clave] || 'SISTEMA LISTO';
    document.getElementById('status').style.boxShadow = clave ? '0 0 15px #00ffcc' : 'none';
    
    // Anima el robot según el giro
    let rot = 0;
    if(pulsadas.has('A')) rot = -25;
    if(pulsadas.has('D')) rot = 25;
    let esc = pulsadas.has('W') ? 1.2 : (pulsadas.has('S') ? 0.8 : 1);
    document.getElementById('icon').style.transform = `rotate(${rot}deg) scale(${esc})`;
  }

  function sendCmd() {
    const cmd = ['W','S','A','D'].filter(k => pulsadas.has(k)).join('') || 'X';
    fetch('/' + cmd).catch(()=>{});
  }

  ['W','S','A','D'].forEach(id => {
    const btn = document.getElementById(id);
    const press = (e) => { e.preventDefault(); pulsadas.add(id); btn.classList.add('activo'); updateUI(); sendCmd(); };
    const release = (e) => { e.preventDefault(); pulsadas.delete(id); btn.classList.remove('activo'); updateUI(); sendCmd(); };
    
    btn.addEventListener('touchstart', press, {passive: false});
    btn.addEventListener('touchend', release, {passive: false});
    btn.addEventListener('touchcancel', release, {passive: false});
    
    // Para PC por si acaso
    btn.addEventListener('mousedown', press);
    window.addEventListener('mouseup', () => { if(pulsadas.has(id)) release({preventDefault:()=>{}}); });
  });
</script>
</body>
</html>"""

    # ==========================================
    # SERVIDOR WEB (SIN LATENCIA)
    # ==========================================
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 8080))
    s.listen(1)
    s.setblocking(False)

    ev3.light.on(Color.GREEN)
    ev3.speaker.beep()
    ev3.screen.clear()
    ev3.screen.print("SERVER ON - MODO RC")
    ev3.screen.print("Abre Chrome:")
    ev3.screen.print("10.230.151.13:8080")
    ev3.screen.print("NO ME PISES PORFA :)")

    VEL_RECTA = 1000
    VEL_GIRO  = 400

    while True:
        try:
            conn, addr = s.accept()
            peticion = conn.recv(1024).decode('utf-8')

            # Combos de botones
            if   'GET /WA' in peticion or 'GET /AW' in peticion: robot.drive(VEL_RECTA, -VEL_GIRO)
            elif 'GET /WD' in peticion or 'GET /DW' in peticion: robot.drive(VEL_RECTA, VEL_GIRO)
            elif 'GET /SA' in peticion or 'GET /AS' in peticion: robot.drive(-VEL_RECTA, -VEL_GIRO)
            elif 'GET /SD' in peticion or 'GET /DS' in peticion: robot.drive(-VEL_RECTA, VEL_GIRO)
            elif 'GET /W'  in peticion: robot.drive(VEL_RECTA, 0)
            elif 'GET /S'  in peticion: robot.drive(-VEL_RECTA, 0)
            elif 'GET /A'  in peticion: robot.drive(0, -VEL_GIRO)
            elif 'GET /D'  in peticion: robot.drive(0, VEL_GIRO)
            else: robot.stop()

            # Enviar la interfaz visual
            if 'GET / ' in peticion:
                conn.send(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                conn.send(HTML_UI.encode())
            else:
                conn.send(b'HTTP/1.1 200 OK\r\n\r\nOK')
            
            conn.close()

        except Exception:
            pass

        wait(10)

except Exception as e:
    ev3.light.on(Color.RED)
    ev3.screen.clear()
    ev3.screen.print("ERROR:")
    ev3.screen.print(str(e))
    wait(10000)