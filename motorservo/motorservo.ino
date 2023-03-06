#include <Servo.h>

#define MOTOR_DRV_IN1 6
#define MOTOR_DRV_IN2 11
#define MOTOR_DRV_IN3 5
#define MOTOR_DRV_IN4 3

#define CAM_SERVO_H 9
#define CAM_SERVO_V 10

#define VOLTAGE_PIN 0
#define VOLTAGE_R1 20000L
#define VOLTAGE_R2 10000L

#define DEVICE_MOTOR_L 1
#define DEVICE_MOTOR_R 2
#define DEVICE_CAM_SERVO_H 3
#define DEVICE_CAM_SERVO_V 4
#define DEVICE_VOLAGE  5

const char CONTROL_MAGICK = 'c';

struct {
    char magick;
    byte device;
    int value;
} control;

Servo camServoH;
Servo camServoV;
unsigned long lastControl = 0;


unsigned int getVoltage() {
    unsigned long vcc = 0,
                  vpin = 0;

    // Read 1.1V reference against AVcc
    // set the reference to Vcc and the measurement to the internal 1.1V reference
    #if defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
        ADMUX = _BV(REFS0) | _BV(MUX4) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
    #elif defined (__AVR_ATtiny24__) || defined(__AVR_ATtiny44__) || defined(__AVR_ATtiny84__)
        ADMUX = _BV(MUX5) | _BV(MUX0);
    #elif defined (__AVR_ATtiny25__) || defined(__AVR_ATtiny45__) || defined(__AVR_ATtiny85__)
        ADMUX = _BV(MUX3) | _BV(MUX2);
    #else
        // works on an Arduino 168 or 328
        ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
    #endif

    delay(3); // Wait for Vref to settle
    ADCSRA |= _BV(ADSC); // Start conversion
    while (bit_is_set(ADCSRA,ADSC)); // measuring

    uint8_t low  = ADCL; // must read ADCL first - it then locks ADCH
    uint8_t high = ADCH; // unlocks both

    // 1.1 * 1023 * 1000 = 1125300
    vcc = 1125300L / ((unsigned long)((high<<8) | low));
    vpin = analogRead(VOLTAGE_PIN);

    // return (vpin * vcc) / 1024 / (VOLTAGE_R2 / (VOLTAGE_R1 + VOLTAGE_R2));
    return (vpin * vcc) / 1024
           * (1000L / (VOLTAGE_R2 * 1000L / (VOLTAGE_R1 + VOLTAGE_R2)));
}

bool readControl() {
   while (true) {
       switch (Serial.peek()) {
           case -1:
               return false;
           case CONTROL_MAGICK:
               break;
           default:
               Serial.read();
               continue;
       }
       break;
   }

   return Serial.readBytes((byte*)&control, sizeof(control))
          == sizeof(control)
          && control.magick == CONTROL_MAGICK;
}

void controlMotor(int in1, int in2) {
    if (control.value > 0) {
        digitalWrite(in1, LOW);
        analogWrite(in2, constrain(control.value, 0, 255));
    } else if (control.value < 0) {
        digitalWrite(in2, LOW);
        analogWrite(in1, constrain(-1 * control.value, 0, 255));
    } else {
        digitalWrite(in1, LOW);
        digitalWrite(in2, LOW);
    }
}

void stopMotors() {
   digitalWrite(MOTOR_DRV_IN1, LOW);
   digitalWrite(MOTOR_DRV_IN2, LOW);
   digitalWrite(MOTOR_DRV_IN3, LOW);
   digitalWrite(MOTOR_DRV_IN4, LOW);
}

void controlCamServo(Servo &servo) {
    servo.write(constrain(control.value, 5, 175));
}

void stopCamServos() {
    camServoH.write(90);
    camServoV.write(90);
}

void controlVoltage() {
    control.value = getVoltage();
    Serial.write((byte*)&control, sizeof(control));
    Serial.flush();
}

void setup() {
    Serial.begin(9600);
    pinMode(MOTOR_DRV_IN1, OUTPUT);
    pinMode(MOTOR_DRV_IN2, OUTPUT);
    pinMode(MOTOR_DRV_IN3, OUTPUT);
    pinMode(MOTOR_DRV_IN4, OUTPUT);
    camServoH.attach(CAM_SERVO_H);
    camServoV.attach(CAM_SERVO_V);
    analogReference(DEFAULT);
    analogWrite(VOLTAGE_PIN, 0);
}

void loop() {
    unsigned long now = millis();
    if (readControl()) {
        lastControl = now;
        digitalWrite(LED_BUILTIN, HIGH);
        switch (control.device) {
            case DEVICE_MOTOR_L:
                controlMotor(MOTOR_DRV_IN1, MOTOR_DRV_IN2);
                break;
            case DEVICE_MOTOR_R:
                controlMotor(MOTOR_DRV_IN3, MOTOR_DRV_IN4);
                break;
            case DEVICE_CAM_SERVO_H:
                controlCamServo(camServoH);
                break;
            case DEVICE_CAM_SERVO_V:
                controlCamServo(camServoV);
                break;
            case DEVICE_VOLAGE:
                controlVoltage();
                break;
        }
    } else {
        if (now - lastControl > 500) {
            digitalWrite(LED_BUILTIN, LOW);
        }
        if (now - lastControl > 3000) {
            // lost control
            stopMotors();
            stopCamServos();
        }
    }
}

// vim:et:ci:pi:sts=0:sw=4:ts=4:ai
