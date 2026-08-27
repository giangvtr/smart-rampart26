#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <OnewireKeypad.h>

// LCD I2C Configuration
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Servo Motor Configuration
Servo gateServo;
const int servoPin = 3; 

// RGB LED Pins Configuration (Pinii 3, 4, 5)
const int rgbRedPin = 2;   // Controls RED
const int rgbGreenPin = 4; // Controls GREEN
const int rgbBluePin = 5;  // Controls BLUE (Not actively used, kept at LOW)

// OnewireKeypad Configuration on Pin A1
char KEYS[] = 
{
	'1', '2', '3', 'A',
	'4', '5', '6', 'B',
	'7', '8', '9', 'C',
	'*', '0', '#', 'D'
};
OnewireKeypad <Print, 16 > Keypad(Serial, KEYS, 4, 4, A1, 4700, 1000);

// Password Variables
String inputCode = "";
const String correctCode = "456";

void setup() {
  Serial.begin(9600);
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  resetDisplay();
  
  // Initialize Servo
  gateServo.attach(servoPin);
  gateServo.write(0); // Starts at 0 degrees (Locked)

  // Initialize RGB Pins
  pinMode(rgbRedPin, OUTPUT);
  pinMode(rgbGreenPin, OUTPUT);
  pinMode(rgbBluePin, OUTPUT);
  
  // Turn everything off at startup
  digitalWrite(rgbRedPin, LOW);
  digitalWrite(rgbGreenPin, LOW);
  digitalWrite(rgbBluePin, LOW);
}

void loop() {
  Keypad.setHoldTime(100);  
  Keypad.setDebounceTime(50); 
  
  // Handle keypad entry
  if (Keypad.keyState() == 3) 
  {
    char keypress = Keypad.getkey();
    if (keypress != '\0') {
      Serial.print("Keypad Key: ");
      Serial.println(keypress);
      
      // Look for numbers only
      if (keypress >= '0' && keypress <= '9') {
        inputCode += keypress;
        
        // Print masking stars (*) across row 2
        lcd.setCursor(inputCode.length() - 1, 1);
        lcd.print("*");
        
        // Verify when 3 digits are successfully typed
        if (inputCode.length() == 3) {
          lcd.clear();
          lcd.setCursor(0, 0);
          
          if (inputCode == correctCode) {
            Serial.println("Access Granted");
            lcd.print("ACCESS GRANTED ");
            gateServo.write(90);
            
            // Rapid blink the GREEN component of the RGB for 3 seconds
            for (int i = 0; i < 10; i++) {
              digitalWrite(rgbGreenPin, HIGH);
              delay(150);
              digitalWrite(rgbGreenPin, LOW);
              delay(150);
            }
            
            gateServo.write(0); // Lock door back
            resetDisplay();
          } 
          else {
            Serial.println("Access Denied");
            lcd.print("WRONG PASSWORD!");
            
            // Rapid blink the RED component of the RGB for 1.5 seconds
            for (int i = 0; i < 5; i++) {
              digitalWrite(rgbRedPin, HIGH);
              delay(150);
              digitalWrite(rgbRedPin, LOW);
              delay(150);
            }
            
            resetDisplay();
          }
          inputCode = ""; // Clear buffer
        }
      }
    }
    while (Keypad.keyState()) {} 
  }
}

void resetDisplay() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enter password:");
  lcd.setCursor(0, 1);
}
