from flask import Flask, render_template, request, jsonify
import serial
import threading
import time
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# --- SETĂRI ---
PORT_SERIAL = 'COM4' # <-- Pune portul tău real (ex: COM4)
EMAIL_SENDER = 'proiectpsnbeleag@gmail.com'  # <-- Pune adresa ta de Gmail
EMAIL_PASSWORD = 'khmq ezsb slrn ccyd'   # <-- Pune parola de 16 litere (fără spații)
EMAIL_RECEIVER = 'proiectpsnbeleag@gmail.com' # <-- Poți pune tot adresa ta, ca să primești alerta la tine
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORT_SERIAL, BAUD_RATE, timeout=1)
    time.sleep(2)
except Exception as e:
    arduino = None
    print(f"Eroare conexiune: {e}")

date_senzori = {"temperatura": "--", "inundatie": "0"}
alerta_email_trimisa = False
# Dicționar în care vom stoca mesajele venite din EEPROM
mesaje_eeprom = {} 

def trimite_email_alerta():
    try:
        msg = EmailMessage()
        msg.set_content("ALARMĂ: Senzorul sistemului a detectat o inundație!")
        msg['Subject'] = '⚠️ ALERTĂ INUNDAȚIE'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("----> Email de alertă expediat!")
    except Exception as e:
        print(f"----> Eroare email: {e}")

def citeste_serial():
    global date_senzori, alerta_email_trimisa, mesaje_eeprom
    while True:
        if arduino and arduino.in_waiting > 0:
            try:
                linie = arduino.readline().decode('utf-8').strip()
                
                # 1. Citim senzorii
                if ";" in linie:
                    parti = linie.split(";")
                    date_senzori["temperatura"] = parti[0]
                    date_senzori["inundatie"] = parti[1]

                    if date_senzori["inundatie"] == "1" and not alerta_email_trimisa:
                        alerta_email_trimisa = True
                        threading.Thread(target=trimite_email_alerta, daemon=True).start()
                    elif date_senzori["inundatie"] == "0" and alerta_email_trimisa:
                        alerta_email_trimisa = False
                
                # 2. Citim mesajele din memorie (Format: "E:index:mesaj")
                elif linie.startswith("E:"):
                    if linie != "E:DONE":
                        parti = linie.split(":", 2)
                        if len(parti) == 3:
                            index_slot = parti[1]
                            text_mesaj = parti[2]
                            mesaje_eeprom[index_slot] = text_mesaj

            except Exception as e:
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
        if actiune == 'on':
            arduino.write(b'A\n')
        elif actiune == 'off':
            arduino.write(b'S\n')
    return jsonify({"status": "ok"})

@app.route('/api/mesaj', methods=['POST'])
def trimite_mesaj():
    data = request.json
    mesaj = data.get('text', '')
    if arduino and mesaj:
        mesaj_scurt = mesaj[:28] 
        comanda = f"M:{mesaj_scurt}\n"
        arduino.write(comanda.encode('utf-8'))
        return jsonify({"status": "succes"})
    return jsonify({"status": "eroare"})

# --- RUTE NOI PENTRU EEPROM ---
@app.route('/api/cere_memorie')
def cere_memorie():
    global mesaje_eeprom
    mesaje_eeprom.clear() # Curățăm lista veche
    if arduino:
        arduino.write(b'C\n') # Trimitem comanda de Citire
    return jsonify({"status": "ok"})

@app.route('/api/memorie')
def get_memorie():
    return jsonify(mesaje_eeprom)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)