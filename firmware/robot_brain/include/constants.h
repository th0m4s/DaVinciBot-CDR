#ifndef CONSTANTS_H
#define CONSTANTS_H

// sch pins: pos_enc_left_a and pos_enc_left_b
#define posInterruptPin_left 25
#define posDirPin_left 26

// sch pins: pos_enc_right_a and pos_enc_right_b
#define posInterruptPin_right 20
#define posDirPin_right 21


#define USE_SPEED_ENCODERS true

// sch pins: speed_enc_left_a and speed_enc_left_b
#define speedInterruptPin_left 27
#define speedDirPin_left 28

// sch pins: speed_enc_right_a and speed_enc_right_b
#define speedInterruptPin_right 18 
#define speedDirPin_right 19


// sch pins: speed_left, speed_right, left_dir_a, left_dir_b, right_dir_a and right_dir_b
#define motorPwm_left 8
#define motorPwm_right 24
#define motorDirA_left 9
#define motorDirB_left 10
#define motorDirA_right 13
#define motorDirB_right 14


#define WHEEL_TICKS_COUNT 1024
// lengths are in mm
#define WHEEL_DISTANCE 275
#define WHEEL_DIAMETER 61

#define ARRIVAL_THRESHOLD 8
#define ROTATION_THRESOLD_DEG 5
#define PT_FWD_THRESHOLD_RAD PI/4

#define MOTORS_V 2
#define MOTORS_K 1

#define ROTATE_SPEED 50

#define ROBOT_ID -1

// because analogRead returns a 10-bit value (from 0 to 1023)
#define ANALOG_WRITE_RESOLUTION 10
// best frequency for a 10-bit resolution on a Teensy 4.1 board (https://www.pjrc.com/teensy/td_pulse.html)
#define ANALOG_WRITE_FREQUENCY 146484.38f



#define PIN_SERVO_1 0
#define PIN_SERVO_2 1
#define PIN_SERVO_3 2
#define PIN_SERVO_4 3
#define PIN_SERVO_5 4
#define PIN_SERVO_6 5

#define PIN_DIN_1 6
#define PIN_DIN_2 7
#define PIN_AIN_1 A8
#define PIN_AIN_2 A9
#endif
