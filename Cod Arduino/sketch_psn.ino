#include <DHT.h>
#include <EEPROM.h>

#define DHTPIN 2          
#define DHTTYPE DHT11     
#define FLOOD_PIN A0      
#define LED_PIN 4         

const int PRAG_INUNDATIE = 200; 

const int LUNGIME_MAX_MESAJ = 30;
const int MAX_MESAJE = 10;
int indexMesajCurent = 0; 

DHT dht(DHTPIN, DHTTYPE);
unsigned long precedentulTimp = 0;
const long intervalCitire = 2000;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  dht.begin();

  indexMesajCurent = EEPROM.read(0);
  if (indexMesajCurent >= MAX_MESAJE || indexMesajCurent < 0) {
    indexMesajCurent = 0;
  }
}

void salveazaInEEPROM(String mesaj) {
  int adresaDeStart = 1 + (indexMesajCurent * LUNGIME_MAX_MESAJ);
  for (int i = 0; i < LUNGIME_MAX_MESAJ - 1; i++) {
    if (i < mesaj.length()) {
      EEPROM.write(adresaDeStart + i, mesaj[i]);
    } else {
      EEPROM.write(adresaDeStart + i, '\0'); 
    }
  }
  indexMesajCurent++;
  if (indexMesajCurent >= MAX_MESAJE) {
    indexMesajCurent = 0; 
  }
  EEPROM.write(0, indexMesajCurent);
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
      for (int i = 0; i < MAX_MESAJE; i++) {
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
