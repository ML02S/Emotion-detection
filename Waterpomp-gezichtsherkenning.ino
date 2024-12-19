// Definieer de pin waar het relais is aangesloten
int relayPin = 5;

void setup() {
  // Stel de pin van het relais in als OUTPUT
  pinMode(relayPin, OUTPUT);
  
  // Seriële communicatie starten om berichten van de Python-code te ontvangen
  Serial.begin(9600);
  
  // Zorg ervoor dat de pomp uitstaat bij het opstarten
  digitalWrite(relayPin, LOW);  // Pomp uit
}

void loop() {
  // Controleer of er gegevens beschikbaar zijn via de seriële poort
  if (Serial.available() > 0) {
    // Lees de ontvangen string (command) van de Python-code
    String command = Serial.readString();
    
    // Controleer of het commando 'WATER_ON' is
    if (command.indexOf("WATER_ON") >= 0) {
      digitalWrite(relayPin, HIGH);  // Zet de pomp aan
      Serial.println("Pomp aan");    // Feedback naar de seriële monitor
    }
    
    // Controleer of het commando 'WATER_OFF' is
    if (command.indexOf("WATER_OFF") >= 0) {
      digitalWrite(relayPin, LOW);  // Zet de pomp uit
      Serial.println("Pomp uit");   // Feedback naar de seriële monitor
    }
  }
}
