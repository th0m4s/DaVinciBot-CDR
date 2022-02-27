#include <Arduino.h>
#include "controllers/BasicMotorController.h"
#include "constants.h"

#define error_int_max 1000

BasicMotorController::BasicMotorController(int leftSpeedPin, int leftDirAPin, int leftDirBPin, int rightSpeedPin, int rightDirAPin, int rightDirBPin) {
    this->leftSpeedPin = leftSpeedPin;
    this->leftDirAPin = leftDirAPin;
    this->leftDirBPin = leftDirBPin;
    this->rightSpeedPin = rightSpeedPin;
    this->rightDirAPin = rightDirAPin;
    this->rightDirBPin = rightDirBPin;
}

void BasicMotorController::stop() {
    analogWrite(leftSpeedPin, 0);
    digitalWrite(leftDirAPin, HIGH);
    digitalWrite(leftDirBPin, LOW);

    analogWrite(rightSpeedPin, 0);
    digitalWrite(rightDirAPin, HIGH);
    digitalWrite(rightDirBPin, LOW);
}

void BasicMotorController::updateOutput(int ticksLeft, int ticksRight, elapsedMillis time) {
    int oldErrorLeft = errorLeft;
    int oldErrorRight = errorRight;

    errorLeft = targetTicksLeftPerSec - (ticksLeft * 1000 / time);
    errorRight = targetTicksRightPerSec - (ticksRight * 1000 / time);

    errorIntLeft += errorLeft;
    errorIntRight += errorRight;

    int _errorIntLeft = errorIntLeft * ki;
    int _errorIntRight = errorIntRight * ki;

    if(_errorIntLeft > error_int_max) {
        _errorIntLeft = error_int_max;
    } else if(_errorIntLeft < -error_int_max) {
        _errorIntLeft = -error_int_max;
    }

    if(_errorIntRight > error_int_max) {
        _errorIntRight = error_int_max;
    } else if(_errorIntRight < -error_int_max) {
        _errorIntRight = -error_int_max;
    }

    int cmdLeft = KP_L * errorLeft + _errorIntLeft + KI_L * _errorIntLeft + KD_L * (errorLeft - oldErrorLeft);
    int cmdRight = KP_R * errorRight + _errorIntRight + KI_R * _errorIntRight + KD_R * (errorRight - oldErrorRight);

    if(cmdLeft >= 0) {
        digitalWrite(leftDirAPin, HIGH);
        digitalWrite(leftDirBPin, LOW);
    } else {
        digitalWrite(leftDirAPin, LOW);
        digitalWrite(leftDirBPin, HIGH);
        cmdLeft = -cmdLeft;
    }

    if(cmdLeft > 1023)
        cmdLeft = 1023;

    analogWrite(leftSpeedPin, cmdLeft);

    if(cmdRight >= 0) {
        digitalWrite(rightDirAPin, HIGH);
        digitalWrite(rightDirBPin, LOW);
    } else {
        digitalWrite(rightDirAPin, LOW);
        digitalWrite(rightDirBPin, HIGH);
        cmdRight = -cmdRight;
    }

    if(cmdRight > 1023)
        cmdRight = 1023;

    analogWrite(rightSpeedPin, cmdRight);
}

void BasicMotorController::setSpeed(double left, double right) {
    targetTicksLeftPerSec = left * WHEEL_TICKS_COUNT;
    targetTicksRightPerSec = right * WHEEL_TICKS_COUNT;
}
