from typing import Union, Tuple
from .. import Action
from .... import api
from ....intercom import intercom_instance as intercom


class ActionRotate(Action):
    """
    Action that rotates a robot to a specific rotation.
    """

    def __init__(self, robot_id: int, rotation: int, center_percentage: int = 50):
        """
        Creates an action to rotate a robot to a given rotation.

        This action finishes when the robot has reached the requested rotation.

        Args:
            robot_id: An integer representing the id of the robot to rotate.
            rotation: The requested rotation of the robot in degrees.
            center_percentage: A percentage (as an integer between 0 and 100) indicating the position of the center of rotation between the wheels.
                The default value is 50, which means the robot will rotate on itself.
        """
        self.robot_id = robot_id
        self.rotation = rotation
        self.center_percentage = center_percentage
        self.registered_ref = -1

        self.done = False

    def start(self) -> None:
        self.registered_ref = intercom.subscribe("robot_arrived", self.__robot_arrived)

    def __robot_arrived(self, robot_id) -> None:
        """
        Internal callback used by intercom when the robot reaches the requested rotation.
        """
        if self.robot_id == robot_id:
            self.done = True

    def tick(self, ticks) -> bool:
        if ticks % 100 == 0:
            # send the messages multiple times in case of the Teensy loses the requested rotation
            api.rotate_robot(self.robot_id, self.rotation, self.center_percentage)

        return self.done  # or ticks > 100  # debug :)

    def finish(self) -> None:
        if self.registered_ref > 0:
            intercom.unsubscribe(self.registered_ref)
