import serial
import time
import requests

# ==========================
# SETĂRILE TALE
# ==========================
PORT_SERIAL = 'COM4'
BAUD_RATE = 9600

# Lipește aici link-ul tău real (fără / la final)
CLOUD_URL = 'https://sistem-iot-david-f3b0d4azf8feehbp.francecentral-01.azurewebsites.net/' 

try:
    # Ne conectăm la placa fizică de pe birou
    arduino = serial.Serial(PORT_SERIAL, BAUD_RATE, timeout=0.1)
    time.sleep(2) 
    print(f"✅ Conectat cu succes la Arduino pe {PORT_SERIAL}")
except Exception as e:
    print(f"❌ Eroare USB: {e}")
    exit()

print(f"🌍 Gateway pornit! Se comunică cu: {CLOUD_URL}")

while True:
    # --- 1. CERE COMENZI DIN CLOUD ȘI LE DĂ LA ARDUINO ---
    try:
        # Întreabă site-ul: "Ai butoane apăsate pe care trebuie să le execut?"
        raspuns = requests.get(f"{CLOUD_URL}/api/get_comenzi", timeout=3)
        if raspuns.status_code == 200:
            comenzi = raspuns.json().get("comenzi", [])
            for comanda in comenzi:
                print(f"📥 Comandă primită din Cloud: {comanda}")
                arduino.write((comanda + '\n').encode('utf-8'))
    except Exception as e:
        pass # Ignorăm erorile de rețea temporare

    # --- 2. CITEȘTE DE LA ARDUINO ȘI TRIMITE ÎN CLOUD ---
    if arduino.in_waiting > 0:
        linie = arduino.readline().decode('utf-8', errors='ignore').strip()
        if linie:
            print(f"📡 Date senzor: {linie}")
            
            # --- ATENȚIE AICI ---
            # Aici aplici logica ta veche de tăiere a textului (split)
            # Presupunem că Arduino trimite ceva de genul "24.5,0"
            try:
                # Adaptează această secțiune la formatul exact trimis de Arduino-ul tău!
                valori = linie.split(',') 
                if len(valori) >= 2:
                    temperatura_citita = valori[0].strip()
                    stare_inundatie = valori[1].strip()
                    
                    # Împachetăm datele
                    date_de_trimis = {
                        "temperatura": temperatura_citita,
                        "inundatie": stare_inundatie
                    }
                    
                    # Le trimitem "poștașului" Azure
                    requests.post(f"{CLOUD_URL}/api/update_senzori", json=date_de_trimis)
                    print("☁️ Date trimise pe site!")
            except Exception as e:
                print(f"⚠️ Eroare la parsarea datelor: {e}")
    
    # O pauză mică pentru a nu bloca procesorul și a nu aglomera serverul Azure
    time.sleep(1)