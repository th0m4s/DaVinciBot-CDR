#include <Arduino.h>

#define MOTOR_A 12
#define MOTOR_B 24
#define ENABLE 25

#define ENC_INPUT 27


IntervalTimer timer;
int ticks = 0;
bool shouldRunLogic = false;
bool testing = false;

#define START_MOTOR_COUNTER 100
#define MAX_RUN_COUNT 500
int runCount = 0;
int data[MAX_RUN_COUNT];

int errorInt = 0;
int lastError = 0;
int targetTicks = 1200;


float kp = 1;
float ki = 0;
float kd = 0;

#define MAX_ERROR_INT 1000

void setup() {
    pinMode(MOTOR_A, OUTPUT);
    pinMode(MOTOR_B, OUTPUT);
    pinMode(ENABLE, OUTPUT);

    pinMode(ENC_INPUT, INPUT);

    digitalWrite(MOTOR_A, LOW);
    digitalWrite(MOTOR_B, LOW);
    attachInterrupt(digitalPinToInterrupt(ENC_INPUT), encoderInterruption, RISING);

    analogWriteResolution(10); // because analogRead returns a 10-bit value (from 0 to 1023)
    analogWriteFrequency(ENABLE, 146484.38f); // best frequency for a 10-bit resolution (https://www.pjrc.com/teensy/td_pulse.html)

    Serial.begin(115200);
    timer.begin(logic, 10*1000); // in microseconds, so 10ms
}

void logic() {
    shouldRunLogic = true;
}

void encoderInterruption() {
    ticks++;
}

void loop() {
    if(!testing && Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        if(command.startsWith("run/")) {
            int end_kp = command.indexOf(" ");
            kp = command.substring(4, end_kp).toFloat();

            int end_ki = command.indexOf(" ", end_kp+1);
            ki = command.substring(end_kp+1, end_ki).toFloat();

            kd = command.substring(end_ki+1).toFloat();

            testing = true;
            runCount = 0;
            ticks = 0;
        }
    }

    if(shouldRunLogic) {
        int ticksCopy = ticks;
        ticks = 0;

        shouldRunLogic = false;

        if(testing) {
            if(runCount == START_MOTOR_COUNTER) {
                digitalWrite(MOTOR_A, HIGH);
                digitalWrite(MOTOR_B, LOW);
            }

            if(runCount < MAX_RUN_COUNT) {
                data[runCount++] = ticksCopy;

                int error = targetTicks - ticksCopy;
                errorInt += (int)(error * ki);

                int _errorInt = errorInt;
                if(_errorInt < MAX_ERROR_INT) {
                    errorInt = MAX_ERROR_INT;
                } else if(_errorInt > -MAX_ERROR_INT) {
                    errorInt = -MAX_ERROR_INT;
                }

                int output = (int)(kp * error + kd * (error - lastError) + errorInt);
                if(output > 1023) {
                    output = 1023;
                } else if(output < 0) {
                    output = 0;
                }

                analogWrite(ENABLE, output);
            } else {
                testing = false;

                digitalWrite(MOTOR_A, LOW);
                digitalWrite(MOTOR_B, LOW);
                analogWrite(ENABLE, 0);

                Serial.print("data/");

                for(int i = 0; i < MAX_RUN_COUNT; i++) {
                    Serial.print(data[i]);
                    Serial.print(" ");
                }

                Serial.println("/done");
                Serial.flush();
            }
        }
    }
}
