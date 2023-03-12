#include <Servo.h>
#include <Adafruit_NeoPixel.h>

#define MOTOR_DRV_IN1 6
#define MOTOR_DRV_IN2 11
#define MOTOR_DRV_IN3 5
#define MOTOR_DRV_IN4 3

#define CAM_SERVO_H 9
#define CAM_SERVO_V 10

#define VOLTAGE_PIN 0
#define VOLTAGE_R1 30000L
#define VOLTAGE_R2 10000L

#define LIGHTING_PIN 4
#define LIGHTING_NUM_PIXELS 8

#define MAGICK_STRING "FpvB"
const char MAGICK[4] = MAGICK_STRING;
#define MAGICK_SIZE sizeof(MAGICK)
#define MAGICK_LEN  (sizeof(MAGICK) / sizeof(MAGICK[0]))

struct {
    char magick[4];
    int motorL,
        motorR,
        camServoH,
        camServoV,
        lighting;
} request;
#define REQUEST_SIZE sizeof(request)

unsigned long requestTime = 0;

struct {
    char magick[4] = MAGICK_STRING;
    int camServoH,
        camServoV,
        voltage;
} response;
#define RESPONSE_SIZE sizeof(response)

Servo camServoH;
Servo camServoV;
int camServoMoveH = 0,
    camServoMoveV = 0;
unsigned long camServoHMoveTime = 0,
              camServoVMoveTime = 0,
              camServoHStartMoveTime = 0,
              camServoVStartMoveTime = 0;
#define CAM_SERVO_POS_BASE 1000

Adafruit_NeoPixel lighting(
    LIGHTING_NUM_PIXELS,
    LIGHTING_PIN,
    NEO_GRB + NEO_KHZ800
);
#define LIGHTING_NUM_STATIC_MODES 8
const byte lightingStaticModes[LIGHTING_NUM_STATIC_MODES][3] = {
    {0x00, 0x00, 0x00}, // 0 - black
    {0x00, 0x00, 0xff}, // 1 - blue
    {0x00, 0xff, 0x00}, // 2 - green
    {0x00, 0xff, 0xff}, // 3 - cyan
    {0xff, 0x00, 0x00}, // 4 - red
    {0xff, 0x00, 0xff}, // 5 - magenta
    {0xff, 0xff, 0x00}, // 6 - yellow
    {0xff, 0xff, 0xff}, // 7 - white
};
int lightingMode = 0;

unsigned int voltage[5] = {0, 0, 0, 0, 0};
#define VOLTAGE_LEN (sizeof(voltage) / sizeof(voltage[0]))
int voltagePos = 0;
unsigned long voltageTime = 0;
unsigned long voltagePosTime = 0;


bool readRequest() {
   int i = 0;

   if (Serial.available() <= MAGICK_SIZE)
       return false;

   while (true) {
       if (Serial.readBytes((byte*)&request.magick[i], 1) != 1)
           return false;

       if (request.magick[i] != MAGICK[i]) {
           if (request.magick[i] == MAGICK[0]) {
               request.magick[0] = MAGICK[0];
               i = 1;
           } else {
               i = 0;
           }
           continue;
       }
       if (++i < MAGICK_LEN)
           continue;
       break;
   }

   return Serial.readBytes(
       ((byte*)&request) + MAGICK_SIZE,
       REQUEST_SIZE - MAGICK_SIZE) == REQUEST_SIZE - MAGICK_SIZE;
}

void controlMotor(int in1, int in2, int value) {
    if (value > 0) {
        digitalWrite(in1, LOW);
        analogWrite(in2, constrain(value, 0, 255));
    } else if (value < 0) {
        digitalWrite(in2, LOW);
        analogWrite(in1, constrain(-1 * value, 0, 255));
    } else {
        digitalWrite(in1, LOW);
        digitalWrite(in2, LOW);
    }
}

void controlCamServo(Servo &servo,
                     int &servoMove,
                     unsigned long &servoMoveStartTime,
                     int value) {
    unsigned long now = millis();

    if (value >= CAM_SERVO_POS_BASE) {
        servo.write(constrain(value - CAM_SERVO_POS_BASE, 5, 175));
        servoMove = 0;
    } else {
        if (value != 0 && value != servoMove)
            servoMoveStartTime = now;
        servoMove = value;
    }
}

void controlCamServoMoveLoop(Servo &servo,
                             int &servoMove,
                             unsigned long &servoMoveTime,
                             unsigned long &servoMoveStartTime) {
    unsigned long now = millis();
    int pause;

    if (servoMove == 0)
        return;

    pause = (now - servoMoveStartTime <= 300) ? 60 : 30;

    if (now - servoMoveTime < pause)
        return;

    servo.write(constrain(servo.read() + servoMove, 5, 175));
    servoMoveTime = now;
}

void controlLighting(int value) {
    if (value >= 0 && value < LIGHTING_NUM_STATIC_MODES) {
        if (value != lightingMode) {
            lighting.clear();
            for (int i = 0; i < LIGHTING_NUM_PIXELS; i++)
                lighting.setPixelColor(
                    i,
                    lighting.Color(
                        lightingStaticModes[value][0],
                        lightingStaticModes[value][1],
                        lightingStaticModes[value][2]
                    )
                );
            lighting.show();
        }
    }
    lightingMode = value;
}

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

void writeResponse() {
    unsigned long vSum = 0;

    if (Serial.availableForWrite() < RESPONSE_SIZE)
        return;

    response.camServoH = CAM_SERVO_POS_BASE + camServoH.read();
    response.camServoV = CAM_SERVO_POS_BASE + camServoV.read();

    for (int i = 0; i < VOLTAGE_LEN; i++) vSum += voltage[i];
    response.voltage = vSum / VOLTAGE_LEN;

    Serial.write((byte*)&response, RESPONSE_SIZE);
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
    lighting.begin();
    lighting.clear();
    lighting.show();
    analogReference(DEFAULT);
    analogWrite(VOLTAGE_PIN, 0);
}

void loop() {
    unsigned long now = millis();
    if (readRequest()) {
        requestTime = now;
        digitalWrite(LED_BUILTIN, HIGH);
        controlMotor(MOTOR_DRV_IN1, MOTOR_DRV_IN2, request.motorL);
        controlMotor(MOTOR_DRV_IN3, MOTOR_DRV_IN4, request.motorR);
        controlCamServo(camServoH,
                        camServoMoveH,
                        camServoHStartMoveTime,
                        request.camServoH);
        controlCamServo(camServoV,
                        camServoMoveV,
                        camServoVStartMoveTime,
                        request.camServoV);
        controlLighting(request.lighting);

        writeResponse();
    } else if (requestTime > 0) {
        if (now - requestTime > 500) {
            digitalWrite(LED_BUILTIN, LOW);
        }
        if (now - requestTime > 3000) {
            // lost control
            controlMotor(MOTOR_DRV_IN1, MOTOR_DRV_IN2, 0);
            controlMotor(MOTOR_DRV_IN3, MOTOR_DRV_IN4, 0);
            controlCamServo(camServoH,
                            camServoMoveH,
                            camServoHStartMoveTime,
                            CAM_SERVO_POS_BASE + 90);
            controlCamServo(camServoV,
                            camServoMoveV,
                            camServoVStartMoveTime,
                            CAM_SERVO_POS_BASE + 90);
            delay(100);
            controlLighting(0);
        }
    }

    controlCamServoMoveLoop(camServoH,
                            camServoMoveH,
                            camServoHMoveTime,
                            camServoHStartMoveTime);
    controlCamServoMoveLoop(camServoV,
                            camServoMoveV,
                            camServoVMoveTime,
                            camServoVStartMoveTime);

    if (now < VOLTAGE_LEN * 100 || now - voltageTime > 60000) {
        if (voltagePos >= VOLTAGE_LEN) {
            voltagePos = 0;
            voltageTime = now;
            voltagePosTime = now;
        } else if (now - voltagePosTime > 50) {
            voltage[voltagePos++] = getVoltage();
            voltagePosTime = now;
        }
    }
}

// vim:et:ci:pi:sts=0:sw=4:ts=4:ai
