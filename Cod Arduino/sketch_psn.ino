#include <DHT.h>
#include <EEPROM.h>

#define DHTPIN 2          
#define DHTTYPE DHT11     
#define FLOOD_PIN A0      
#define LED_PIN 4         

const int PRAG_INUNDATIE = 200; 

const int LUNGIME_MAX_MESAJ = 30;
const int MAX_MESAJE = 10;
int nrMesaje = 0; // Va ține minte strict câte mesaje avem stocate

DHT dht(DHTPIN, DHTTYPE);
unsigned long precedentulTimp = 0;
const long intervalCitire = 2000;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  dht.begin();

  // Citim de la adresa 0 câte mesaje avem
  nrMesaje = EEPROM.read(0);
  if (nrMesaje > MAX_MESAJE || nrMesaje < 0) {
    nrMesaje = 0; // Dacă e corupt sau prima rulare, resetăm numărătoarea
  }
}

void salveazaInEEPROM(String mesaj) {
  if (nrMesaje == MAX_MESAJE) {
    // MEMORIA E PLINĂ: Mutăm toate mesajele cu o poziție mai sus (spre stânga)
    for (int i = 0; i < MAX_MESAJE - 1; i++) {
      int adresaDestinatie = 1 + (i * LUNGIME_MAX_MESAJ);
      int adresaSursa = 1 + ((i + 1) * LUNGIME_MAX_MESAJ);
      
      for (int j = 0; j < LUNGIME_MAX_MESAJ; j++) {
        // Folosim update() pentru a proteja viața memoriei
        EEPROM.update(adresaDestinatie + j, EEPROM.read(adresaSursa + j));
      }
    }
    // După mutare, "eliberăm" ultima poziție pentru noul mesaj
    nrMesaje = MAX_MESAJE - 1;
  }

  // Salvăm noul mesaj la indexul curent (care va fi ultimul)
  int adresaDeStart = 1 + (nrMesaje * LUNGIME_MAX_MESAJ);
  for (int i = 0; i < LUNGIME_MAX_MESAJ - 1; i++) {
    if (i < mesaj.length()) {
      EEPROM.update(adresaDeStart + i, mesaj[i]);
    } else {
      EEPROM.update(adresaDeStart + i, '\0'); 
    }
  }
  
  // Creștem numărul de mesaje și îl salvăm la adresa 0
  nrMesaje++; 
  EEPROM.update(0, nrMesaje); 
}

void loop() {
  if (Serial.available() > 0) {
    String comandaPrimita = Serial.readStringUntil('\n');
    comandaPrimita.trim(); 
    
    if (comandaPrimita == "A") {
      digitalWrite(LED_PIN, HIGH);
    } 
    else if (comandaPrimita == "S") {
      digitalWrite(LED_PIN, LOW);
    }
    else if (comandaPrimita.startsWith("M:")) {
      String textMesaj = comandaPrimita.substring(2); 
      salveazaInEEPROM(textMesaj);
    }
    else if (comandaPrimita == "C") {
      // Citim strict câte mesaje avem (nu mai trimitem sloturi goale către PC)
      for (int i = 0; i < nrMesaje; i++) {
        int adresaDeStart = 1 + (i * LUNGIME_MAX_MESAJ);
        String mesajCitit = "";
        
        for (int j = 0; j < LUNGIME_MAX_MESAJ - 1; j++) {
          char litera = EEPROM.read(adresaDeStart + j);
          if (litera == '\0' || litera == 255) break; 
          mesajCitit += litera;
        }
        
        if (mesajCitit.length() > 0) {
          Serial.print("MEM:");
          Serial.print(i);
          Serial.print(":");
          Serial.println(mesajCitit);
        }
      }
      Serial.println("GATA_MEMORIE");
    }
  }

  // --- Citirea senzorilor ---
  unsigned long timpulCurent = millis();
  if (timpulCurent - precedentulTimp >= intervalCitire) {
    precedentulTimp = timpulCurent;

    float temperatura = dht.readTemperature();
    int valoareInundatie = analogRead(FLOOD_PIN);
    bool esteInundatie = (valoareInundatie > PRAG_INUNDATIE);

    if (isnan(temperatura)) { temperatura = -999; }

    Serial.print(temperatura);
    Serial.print(";");
    Serial.println(esteInundatie ? "1" : "0");
  }
}
