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
#define DEVICE_CAM_SERVO_MOVE_H 5
#define DEVICE_CAM_SERVO_MOVE_V 6
#define DEVICE_VOLAGE  7

const char CONTROL_MAGICK[4] = "FpvB";
#define CONTROL_MAGICK_SIZE sizeof(CONTROL_MAGICK)
#define CONTROL_MAGICK_LEN  (sizeof(CONTROL_MAGICK) / sizeof(CONTROL_MAGICK[0]))

struct {
    char magick[4];
    int device;
    int value;
} control;

#define CONTROL_SIZE sizeof(control)
#define CONTROL_NO_MAGICK_SIZE (sizeof(control) - sizeof(CONTROL_MAGICK))

Servo camServoH;
Servo camServoV;
int camServoMoveH = 0,
    camServoMoveV = 0;
unsigned long servoTime = 0;
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
   int i = 0;

   if (Serial.available() <= CONTROL_MAGICK_SIZE)
       return false;

   while (true) {
       if (Serial.readBytes((byte*)&control.magick[i], 1) != 1)
           return false;

       if (control.magick[i] != CONTROL_MAGICK[i]) {
           if (control.magick[i] == CONTROL_MAGICK[0]) {
             control.magick[0] = CONTROL_MAGICK[0];
             i = 1;
           } else {
             i = 0;
           }
           continue;
       }
       if (++i < CONTROL_MAGICK_LEN)
           continue;
       break;
   }

   return Serial.readBytes(
       ((byte*)&control) + CONTROL_MAGICK_SIZE,
       CONTROL_NO_MAGICK_SIZE) == CONTROL_NO_MAGICK_SIZE;
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

void controlCamServoMove(int &mv) {
    mv = control.value;
}

void controlCamServoMoveLoop(Servo &servo, int &mv) {
    if (mv != 0)
        servo.write(constrain(servo.read() + mv, 5, 175));
}

void resetCamServo(Servo &servo, int &mv) {
    servo.write(90);
    mv = 0;
}

void controlVoltage() {
    control.value = getVoltage();
    Serial.write((byte*)&control, CONTROL_SIZE);
}

void setup() {
    Serial.begin(9600);
    Serial.setTimeout(100);
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
            case DEVICE_CAM_SERVO_MOVE_H:
                controlCamServoMove(camServoMoveH);
                break;
            case DEVICE_CAM_SERVO_MOVE_V:
                controlCamServoMove(camServoMoveV);
                break;
            case DEVICE_VOLAGE:
                controlVoltage();
                break;
        }
    } else if (lastControl > 0) {
        if (now - lastControl > 500) {
            digitalWrite(LED_BUILTIN, LOW);
        }
        if (now - lastControl > 3000) {
            // lost control
            stopMotors();
            resetCamServo(camServoH, camServoMoveH);
            resetCamServo(camServoV, camServoMoveV);
        }
    }

    if (now - servoTime > 30) {
        controlCamServoMoveLoop(camServoH, camServoMoveH);
        controlCamServoMoveLoop(camServoV, camServoMoveV);
        servoTime = now;
    }
}

// vim:et:ci:pi:sts=0:sw=4:ts=4:ai
