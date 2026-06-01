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
            print(f"📡 Date primite: {linie}")
            
            # CAZUL A: Am primit un mesaj din memorie
            if linie.startswith("MEM:"):
                parti = linie.split(":", 2) # Tăiem textul în 3 bucăți
                if len(parti) == 3:
                    index_mesaj = parti[1]
                    text_mesaj = parti[2]
                    # Dacă nu există dicționarul, îl creăm ad-hoc
                    if 'memorie_temporara' not in globals():
                        globals()['memorie_temporara'] = {}
                    memorie_temporara[f"Mesajul {index_mesaj + 1}: "] = text_mesaj
            
            # CAZUL B: Arduino a terminat de citit memoria
            elif linie == "GATA_MEMORIE":
                if 'memorie_temporara' in globals() and memorie_temporara:
                    # Aruncăm pachetul de mesaje pe serverul Azure
                    requests.post(f"{CLOUD_URL}/api/update_memorie", json=memorie_temporara)
                    print("💾 Memorie trimisă cu succes în Cloud!")
                    memorie_temporara.clear() # Golim pentru data viitoare
                else:
                    print("ℹ️ Memoria EEPROM este goală.")
                    requests.post(f"{CLOUD_URL}/api/update_memorie", json={"Info": "Niciun mesaj salvat în memoria hardware."})
                    
            # CAZUL C: Am primit date de la senzori (conțin punct și virgulă)
            elif ";" in linie:
                try:
                    valori = linie.split(';') 
                    if len(valori) >= 2:
                        date_de_trimis = {
                            "temperatura": valori[0].strip(),
                            "inundatie": valori[1].strip()
                        }
                        requests.post(f"{CLOUD_URL}/api/update_senzori", json=date_de_trimis)
                        print("☁️ Date senzori trimise pe site!")
                except Exception as e:
                    print(f"⚠️ Eroare la senzori: {e}")
    
    # O pauză mică pentru a nu bloca procesorul și a nu aglomera serverul Azure
    time.sleep(1)