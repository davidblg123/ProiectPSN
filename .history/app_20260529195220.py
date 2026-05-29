from flask import Flask, render_template, request, jsonify
import threading
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# --- SETĂRI EMAIL ---
EMAIL_SENDER = 'proiectpsnbeleag@gmail.com'
EMAIL_PASSWORD = 'khmq ezsb slrn ccyd'
EMAIL_RECEIVER = 'proiectpsnbeleag@gmail.com'

# --- MEMORIA VIRTUALĂ A CLOUD-ULUI ---
date_senzori = {"temperatura": "--", "inundatie": "0"}
mesaje_eeprom = {}
comenzi_pendinte = [] # Aici se stochează comenzile ("A", "S", "C") până le preia PC-ul tău
alerta_email_trimisa = False

def trimite_email_alerta():
    try:
        msg = EmailMessage()
        msg.set_content("ALARMĂ: Senzorul sistemului a detectat o inundație!")
        msg['Subject'] = '⚠️ ALERTĂ INUNDAȚIE - Cloud Azure'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("----> Email trimis din Cloud!")
    except Exception as e:
        print(f"----> Eroare email: {e}")

@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# RUTE PENTRU INTERFAȚA WEB (Ce accesezi tu)
# ==========================================
@app.route('/api/date', methods=['GET'])
def get_date():
    return jsonify(date_senzori)

@app.route('/led/<actiune>')
def control_led(actiune):
    if actiune == 'on':
        comenzi_pendinte.append('A')
    elif actiune == 'off':
        comenzi_pendinte.append('S')
    return jsonify({"status": "ok"})

@app.route('/api/mesaj', methods=['POST'])
def trimite_mesaj():
    data = request.json
    mesaj = data.get('text', '')
    if mesaj:
        mesaj_scurt = mesaj[:28] 
        comenzi_pendinte.append(f"M:{mesaj_scurt}")
        return jsonify({"status": "succes"})
    return jsonify({"status": "eroare"})

@app.route('/api/cere_memorie')
def cere_memorie():
    global mesaje_eeprom
    mesaje_eeprom.clear() 
    comenzi_pendinte.append('C')
    return jsonify({"status": "ok"})

@app.route('/api/memorie', methods=['GET'])
def get_memorie():
    return jsonify(mesaje_eeprom)

# ==========================================
# RUTE PENTRU PC-UL TĂU (GATEWAY IOT)
# ==========================================
@app.route('/api/update_senzori', methods=['POST'])
def update_senzori():
    global date_senzori, alerta_email_trimisa
    data = request.json
    if data:
        date_senzori["temperatura"] = data.get("temperatura", date_senzori["temperatura"])
        noua_stare_inundatie = data.get("inundatie", date_senzori["inundatie"])
        date_senzori["inundatie"] = noua_stare_inundatie
        
        # Trimitem email automat dacă s-a udat senzorul
        if noua_stare_inundatie == "1" and not alerta_email_trimisa:
            alerta_email_trimisa = True
            threading.Thread(target=trimite_email_alerta, daemon=True).start()
        elif noua_stare_inundatie == "0" and alerta_email_trimisa:
            alerta_email_trimisa = False
            
    return jsonify({"status": "ok"})

@app.route('/api/update_memorie', methods=['POST'])
def update_memorie():
    global mesaje_eeprom
    data = request.json
    if data:
        mesaje_eeprom = data
    return jsonify({"status": "ok"})

@app.route('/api/get_comenzi', methods=['GET'])
def get_comenzi():
    global comenzi_pendinte
    comenzi_de_trimis = list(comenzi_pendinte)
    comenzi_pendinte.clear() # Le ștergem după ce le-am dat PC-ului
    return jsonify({"comenzi": comenzi_de_trimis})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)