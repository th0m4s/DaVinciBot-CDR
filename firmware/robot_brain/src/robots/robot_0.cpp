#ifdef ROBOT_0
#include <Arduino.h>
#include "constants.h"
#include "robot.h"
#include "intercom.h"

#define KP_L 1
#define KI_L 0
#define KD_L 0

#define KP_R 1
#define KI_R 0
#define KD_R 0

String robot_name = "robot_0";

int excavation_known_resistor = 750; // ohms
int excavation_voltage_input = PIN_AIN_1;

void robot_setup() {
    Intercom::registerSensor("excavation_read_sensor");

    pinMode(excavation_voltage_input, INPUT);
}

void robot_logic() {

}

void robot_loop() {
    int readId;

    if(Intercom::isSensorRequested("excavation_read_sensor", &readId)) {
        int value = analogRead(excavation_voltage_input);
        int resistor = (1024.0 / value - 1) * excavation_known_resistor;
        Intercom::sendSensorValue("excavation_read_sensor", readId, resistor);
    }
}
#endif