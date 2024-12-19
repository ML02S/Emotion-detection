const int relayPin = 5;  // Pin waarop het relais is aangesloten

void setup() {
  pinMode(relayPin, OUTPUT);
  Serial.begin(9600);  // Start seriële communicatie
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');  // Lees het commando van de seriële poort

    if (command == "WATER_ON") {
      digitalWrite(relayPin, HIGH);  // Zet de pomp aan
    } 
    else if (command == "WATER_OFF") {
      digitalWrite(relayPin, LOW);   // Zet de pomp uit
    }
  }
}
