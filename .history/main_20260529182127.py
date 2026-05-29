from flask import Flask, render_template, request, jsonify
import serial
import threading
import time

app = Flask(__name__)

# SCHIMBĂ COM3 CU PORTUL TĂU REAL (ex: 'COM4')
PORT_SERIAL = 'COM4'
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORT_SERIAL, BAUD_RATE, timeout=1)
    time.sleep(2)
except Exception as e:
    arduino = None
    print(f"Eroare: Nu m-am putut conecta: {e}")

date_senzori = {"temperatura": "--", "inundatie": "0"}

def citeste_serial():
    global date_senzori
    while True:
        if arduino and arduino.in_waiting > 0:
            try:
                linie = arduino.readline().decode('utf-8').strip()
                if ";" in linie:
                    parti = linie.split(";")
                    date_senzori["temperatura"] = parti[0]
                    date_senzori["inundatie"] = parti[1]
            except:
                pass
        time.sleep(0.1)

thread = threading.Thread(target=citeste_serial, daemon=True)
thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/date')
def get_date():
    return jsonify(date_senzori)

@app.route('/led/<actiune>')
def control_led(actiune):
    if arduino:
        # Acum trimitem cu \n la final ca să poată fi citit de Arduino
        if actiune == 'on':
            arduino.write(b'A\n')
        elif actiune == 'off':
            arduino.write(b'S\n')
    return jsonify({"status": "ok"})

# RUTĂ NOUĂ PENTRU A TRIMITE MESAJE
@app.route('/api/mesaj', methods=['POST'])
def trimite_mesaj():
    data = request.json
    mesaj = data.get('text', '')
    
    if arduino and mesaj:
        # Ne asigurăm că mesajul nu e prea lung
        mesaj_scurt = mesaj[:28] 
        # Punem eticheta "M:" în față, recunoscută de Arduino
        comanda = f"M:{mesaj_scurt}\n"
        arduino.write(comanda.encode('utf-8'))
        return jsonify({"status": "succes"})
        
    return jsonify({"status": "eroare"})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)