from flask import Flask, render_template, request, jsonify
import serial
import threading
import time
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# --- SETĂRI CONEXIUNE ȘI EMAIL ---
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
    print(f"Eroare conexiune Arduino: {e}")

date_senzori = {"temperatura": "--", "inundatie": "0"}
alerta_email_trimisa = False # Ne asigurăm că nu trimitem spam

# Funcția care trimite efectiv email-ul
def trimite_email_alerta():
    try:
        msg = EmailMessage()
        msg.set_content("ALARMĂ: Senzorul sistemului a detectat o inundație!")
        msg['Subject'] = '⚠️ ALERTĂ INUNDAȚIE - Proiect Sincretic'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("----> Email de alertă expediat cu succes!")
    except Exception as e:
        print(f"----> Eroare la trimiterea emailului: {e}")

def citeste_serial():
    global date_senzori, alerta_email_trimisa
    while True:
        if arduino and arduino.in_waiting > 0:
            try:
                linie = arduino.readline().decode('utf-8').strip()
                if ";" in linie:
                    parti = linie.split(";")
                    date_senzori["temperatura"] = parti[0]
                    date_senzori["inundatie"] = parti[1]

                    # Logica pentru declanșarea alarmei pe email
                    if date_senzori["inundatie"] == "1" and not alerta_email_trimisa:
                        alerta_email_trimisa = True # Ridicăm steagul
                        # Pornim trimiterea în fundal ca să nu blocăm citirea datelor
                        threading.Thread(target=trimite_email_alerta, daemon=True).start()
                    
                    elif date_senzori["inundatie"] == "0" and alerta_email_trimisa:
                        alerta_email_trimisa = False # Resetăm steagul când se usucă senzorul

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

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)