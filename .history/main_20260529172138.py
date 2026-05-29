from flask import Flask, render_template, request, jsonify
import serial
import threading
import time

app = Flask(__name__)

# Configurare port serial (SCHIMBĂ COM3 CU PORTUL TĂU REAL, ex: 'COM4')
PORT_SERIAL = 'COM4'
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORT_SERIAL, BAUD_RATE, timeout=1)
    time.sleep(2) # Așteptăm puțin să se inițializeze conexiunea
except Exception as e:
    arduino = None
    print(f"Eroare: Nu m-am putut conecta la Arduino pe {PORT_SERIAL}. Detalii: {e}")

# Variabilă globală în care vom stoca ultimele date citite
date_senzori = {"temperatura": "--", "inundatie": "0"}

# Funcție care rulează în fundal și citește continuu de la Arduino
def citeste_serial():
    global date_senzori
    while True:
        if arduino and arduino.in_waiting > 0:
            try:
                linie = arduino.readline().decode('utf-8').strip()
                # Ne așteptăm la formatul "28.50;0"
                if ";" in linie:
                    parti = linie.split(";")
                    date_senzori["temperatura"] = parti[0]
                    date_senzori["inundatie"] = parti[1]
            except:
                pass
        time.sleep(0.1)

# Pornim citirea în fundal
thread = threading.Thread(target=citeste_serial, daemon=True)
thread.start()

@app.route('/')
def index():
    # Caută automat fișierul index.html în folderul "templates"
    return render_template('index.html')

@app.route('/api/date')
def get_date():
    # Trimite datele către pagina web sub formă de JSON
    return jsonify(date_senzori)

@app.route('/led/<actiune>')
def control_led(actiune):
    # Trimite comenzi către Arduino
    if arduino:
        if actiune == 'on':
            arduino.write(b'A')
        elif actiune == 'off':
            arduino.write(b'S')
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)