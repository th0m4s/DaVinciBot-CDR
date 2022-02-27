from typing import Tuple, Union
from dvbcdr.intercom import intercom_instance as intercom


def move_robot(robot_id: int, position: Union[Tuple[int, int], Tuple[int, int, int]], backwards=False) -> None:
    """
    Moves a robot to a given position on the table.

    Args:
        robot_id: An integer representing the id of the robot to move.
        position: A tuple of integers representing the position in mm to move the robot to.
            If the tuple has 3 elements, it will indicate the rotation (in degrees) the robot should be in after arriving.
        backwards: If True, the robot will move backwards. Default value is False.
    """

    intercom.publish("robot_backwards", [robot_id, int(backwards)])

    if len(position) == 2:
        position = (*position, -1)

    intercom.publish("move_robot", [robot_id, *position])


def rotate_robot(robot_id: int, rotation: int, center_percentage: int = 50) -> None:
    """
    Rotates a robot to a specific angle.

    Args:
        robot_id: An integer representing the id of the robot to rotate.
        rotation: The rotation in degrees the robot should be in.
        center_percentage: A percentage (as an integer between 0 and 100) representing the center of rotation as a percentage between the wheels.
            The default value is 50, which means the robot will rotate on itself.
    """
    if center_percentage < 0:
        center_percentage = 0
    elif center_percentage > 100:
        center_percentage = 100

    intercom.publish("move_robot", [robot_id, rotation, center_percentage])


def move_servo(servo_id: Union[str, int], angle: int) -> None:
    """
    Moves a servo to a given angle.

    Args:
        servo_id: The id (string or int) of the servo to move.
        angle: An integer representing the angle to move the servo to in degrees.
    """
    intercom.publish("api_request_servo" + str(servo_id), int(angle))


read_sensors = {}


def __received_sensor_value(read_id: int, sensor_value: Union[int, float]) -> None:
    """
    Internal callback called by intercom when a sensor value is received.
    """
    read_sensors[read_id] = sensor_value
    intercom.unsubscribe(read_id)


def request_sensor_value(sensor_id: Union[str, int]) -> int:
    """
    Requests a value from a sensor. The type of value is determined by the implementation of the registered handler.

    WARNING: This does not return a value read from the sensor but an intercom callback id required to read the value.

    Args:
        sensor_id: The id of the sensor to request the value from.

    Returns:
        A integer that unically identifies the request. Pass this value to `access_sensor_value` to later read the value.
    """
    read_id = intercom.subscribe("api_response_sensor" + str(sensor_id), lambda message: __received_sensor_value(int(message[0]), message[1]))
    intercom.publish("api_request_sensor" + str(sensor_id), read_id)
    return read_id


def access_sensor_value(read_id, autodelete=True) -> Union[int, float]:
    """
    Returns the value read from the sensor from a given read_id returned by `request_sensor_value`.

    Args:
        read_id: The request id returned by `request_sensor_value`.
        autodelete: If True (default), the the value will be deleted from the cache of sensor responses.

    Returns:
        An int or float value read from the sensor.
    """
    if read_id in read_sensors:
        value = read_sensors[read_id]
        if autodelete:
            del read_sensors[read_id]
        return value
