#include "intercom.h"
#include "constants.h"
#include "robot.h"
#include "controllers/BasicMotorController.h"

#include <Arduino.h>
#include <math.h>


int posTicksLeft = 0;
int posTicksRight = 0;

int speedTicksLeft = 0;
int speedTicksRight = 0;

double robot_transform[3];
double* robot_x = &robot_transform[0];
double* robot_y = &robot_transform[1];
double* robot_teta = &robot_transform[2];

// "all" arrays send to and received from intercom are 1-indexed
// (0 is reserved for the robot's id)
int transform_approx[4];

void posInterruptionLeft() {
    if (digitalReadFast(posDirPin_left)) {
        posTicksLeft++;
    } else {
        posTicksLeft--;
    }
}

void posInterruptionRight() {
    if (!digitalReadFast(posDirPin_right)) {
        posTicksRight++;
    } else {
        posTicksRight--;
    }
}

void speedInterruptionLeft() {
    if (digitalReadFast(speedDirPin_left)) {
        speedTicksLeft++;
    } else {
        speedTicksLeft--;
    }
}

void speedInterruptionRight() {
    if (!digitalReadFast(speedDirPin_right)) {
        speedTicksRight++;
    } else {
        speedTicksRight--;
    }
}

void updatePosition(double dleft, double dright) {
    double dcenter = (dleft + dright) / 2;
    double phi = (dright - dleft) / WHEEL_DIAMETER;
    double half = *robot_teta + phi / 2;
    
    *robot_x = *robot_x + dcenter * cos(half);
    *robot_y = *robot_y + dcenter * sin(half);
    *robot_teta = *robot_teta + phi;

    while(*robot_teta > PI) {
        *robot_teta -= 2 * PI;
    }

    while(*robot_teta < -PI) {
        *robot_teta += 2 * PI;
    }

    transform_approx[1] = (int) *robot_x;
    transform_approx[2] = (int) *robot_y;
    transform_approx[3] = (int) (*robot_teta * RAD_TO_DEG);
}

IMotorController* motorController;
IntervalTimer timer;
elapsedMillis time;

bool shouldRunLogic = false;
void logic() {
    shouldRunLogic = true;
}

void setup() {
    Intercom::init("brain_" + robot_name, DEFAULT_INTERCOM_SPEED);

    Intercom::subscribe("force_robot_position");
    Intercom::subscribe("move_robot");
    Intercom::subscribe("rotate_robot");

    transform_approx[0] = ROBOT_ID;

    pinMode(posInterruptPin_left, INPUT_PULLDOWN);
    pinMode(posInterruptPin_right, INPUT_PULLDOWN);
    pinMode(posDirPin_left, INPUT_PULLDOWN);
    pinMode(posDirPin_right, INPUT_PULLDOWN);

    attachInterrupt(digitalPinToInterrupt(posInterruptPin_left), posInterruptionLeft, CHANGE);
    attachInterrupt(digitalPinToInterrupt(posInterruptPin_right), posInterruptionRight, CHANGE);

    if(USE_SPEED_ENCODERS) {
        pinMode(speedInterruptPin_left, INPUT_PULLDOWN);
        pinMode(speedInterruptPin_right, INPUT_PULLDOWN);
        pinMode(speedDirPin_left, INPUT_PULLDOWN);
        pinMode(speedDirPin_right, INPUT_PULLDOWN);

        attachInterrupt(digitalPinToInterrupt(speedInterruptPin_left), speedInterruptionLeft, CHANGE);
        attachInterrupt(digitalPinToInterrupt(speedInterruptPin_right), speedInterruptionRight, CHANGE);
    }

    // NVIC_SET_PRIORITY(IRQ_PORTA, 0);

    pinMode(motorPwm_left, OUTPUT);
    pinMode(motorPwm_right, OUTPUT);
    pinMode(motorDirA_left, OUTPUT);
    pinMode(motorDirB_left, OUTPUT);
    pinMode(motorDirA_right, OUTPUT);
    pinMode(motorDirB_right, OUTPUT);

    digitalWrite(motorPwm_left, LOW);
    digitalWrite(motorPwm_right, LOW);
    digitalWrite(motorDirA_left, LOW);
    digitalWrite(motorDirB_left, LOW);
    digitalWrite(motorDirA_right, LOW);
    digitalWrite(motorDirB_right, LOW);

    motorController = new BasicMotorController(1, 2, 3, 4, 5, 6);

    timer.begin(logic, 10*1000); // in microseconds, so 10ms
    time = 0;

    robot_setup();
}

const float constDist = PI * WHEEL_DIAMETER / WHEEL_TICKS_COUNT;

int requested_position[3];
int* req_x = &requested_position[0];
int* req_y = &requested_position[1];
int* req_teta = &requested_position[2];
int rotation_center_percentage = 50;
bool follow_requested_position = true;
bool arrived_sent = false;

int* last_received_position;
int last_received_length;

int distance(int xa, int ya, int xb, int yb) {
    return sqrt(pow(xa - xb, 2) + pow(ya - yb, 2));
}

double anglePi(double angle) {
    while(angle >= 2*PI) {
        angle -= 2 * PI;
    }

    while(angle < 0) {
        angle += 2 * PI;
    }

    return angle;
}

void loop() {
    Intercom::tick();

    if(Intercom::instantHasReceivedEvent("stop")) {
        arrived_sent = true;
        motorController->stop();

        requested_position[0] = transform_approx[1];
        requested_position[1] = transform_approx[2];
        requested_position[2] = transform_approx[3];
    }

    if(shouldRunLogic) {
        shouldRunLogic = false;
        // run logic at a specific rate per second

        updatePosition(constDist * posTicksLeft, constDist * posTicksRight);
        Intercom::publish("robot_position", transform_approx, 4);

        if(Intercom::instantReceiveIntArray("move_robot", last_received_position, &last_received_length)) {
            // element 0 (first position) is the robot id, so position starts at element 1
            if(last_received_length == 4 && last_received_position[0] == ROBOT_ID) {
                requested_position[0] = last_received_position[1];
                requested_position[1] = last_received_position[2];
                requested_position[2] = last_received_position[3]; // send a negative rotation if not required
                rotation_center_percentage = 50;

                follow_requested_position = true;
                arrived_sent = false;
            }
        }

        if(Intercom::instantReceiveIntArray("force_robot_position", last_received_position, &last_received_length)) {
            // element 0 (first position) is the robot id, so position starts at element 1
            if(last_received_length == 4 && last_received_position[0] == ROBOT_ID) {
                *robot_x = last_received_position[1];
                *robot_y = last_received_position[2];
                *robot_teta = last_received_position[3] * DEG_TO_RAD;
            }
        }

        if(Intercom::instantReceiveIntArray("rotate_robot", last_received_position, &last_received_length)) {
            // here we are just using the last_received_position array to store the rotation and the center percentage
            if((last_received_length == 2 || last_received_length == 3) && last_received_position[0] == ROBOT_ID) {
                requested_position[2] = last_received_position[1];

                if(last_received_length == 3) {
                    rotation_center_percentage = last_received_position[2];

                    if(rotation_center_percentage < 0) {
                        rotation_center_percentage = 0;
                    } else if(rotation_center_percentage > 100) {
                        rotation_center_percentage = 100;
                    }
                } else {
                    rotation_center_percentage = 50;
                }

                // if center_percentage is not 50, the robot will move by rotating, so we don't want to move back
                follow_requested_position = false;

                arrived_sent = false;
            }
        }

        int dist = 0;
        if(follow_requested_position) {
            dist = distance(transform_approx[1], transform_approx[2], requested_position[0], requested_position[1])
        } // if we don't want to follow the requested position, dist will be 0, hence `arrived` will be true

        double angle_difference = atan2(requested_position[1] - transform_approx[2], requested_position[0] - transform_approx[1]) - transform_approx[3];
        bool arrived = dist <= ARRIVAL_THRESHOLD;

        if(!arrived && abs(angle_difference) <= PT_FWD_THRESHOLD_RAD) {
            // if we are not arrived and the angle is not too large, we can move using the point forward steering controller
            // angle = anglePi(angle);

            double cos_angle = cos(angle_difference);
            double sin_angle = sin(angle_difference);

            motorController->setSpeed(MOTORS_V * (cos_angle + MOTORS_K * sin_angle), MOTORS_V * (cos_angle - MOTORS_K * sin_angle));
        } else {
            int requested_angle = arrived ? requested_position[2] : (anglePi(angle_difference) * RAD_TO_DEG);
            // we need to rotate, either because of an angle at arrival or because of a large angle difference

            // as this is a request from a raspberry, values are integers and cannot be stored in radians
            if(requested_angle >= 0 && requested_angle < 360) {
                int current_angle = (int) (*robot_teta * RAD_TO_DEG);

                if(abs(current_angle - requested_angle) > ROTATION_THRESOLD_DEG) {
                    int direction = current_angle > requested_angle ? 1 : -1;
                    float center_perc = (float) rotation_center_percentage / 100.0;

                    motorController->setSpeed(ROTATE_SPEED * direction * 2 * center_perc, ROTATE_SPEED * -direction * 2 * (1 - center_perc));
                } else {
                    // our orientation is correct, we stop the motors
                    motorController->setSpeed(0, 0);
                    
                    if(!arrived_sent) {
                        arrived_sent = true;
                        Intercom::publish("robot_arrived", ROBOT_ID);
                    }
                }
            } else {
                // we don't want a specific orientation so we stop
                motorController->setSpeed(0, 0);

                if(!arrived_sent) {
                    arrived_sent = true;
                    Intercom::publish("robot_arrived", ROBOT_ID);
                }
            }
        }

        motorController->updateOutput(speedTicksLeft, speedTicksRight, time);
        time = 0;

        posTicksRight = 0;
        posTicksLeft = 0;

        robot_logic();
    }

    robot_loop();
}