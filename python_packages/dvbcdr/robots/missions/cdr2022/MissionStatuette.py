from ...robot import RobotSide
from .. import Mission
from ...actions import ActionMove, ActionServo


class MissionStatuette(Mission):
    positions = [
        # TODO: robot positions
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.add_actions()

        # there is not a lot a space in the corner of the table, maybe we should add a percentage to the rotate_robot message:
        # it would position the center of rotation at a certain percentage between the 2 wheels. default would be 50%

    # TODO: why this method is not in the Mission class? the side check is always the same...
    def __get_move_action(self, index, backwards=False, backwards_if_side=None):
        position = self.positions[index]
        return ActionMove(self.robot.id, (position[0] if self.robot.side == RobotSide.LEFT else 3000 - position[0], position[1]), backwards=(backwards or backwards_if_side == self.robot.side))

    def __arm_down_action(self):
        pass

    def __arm_grab_actions(self):
        pass

    def __arm_release_actions(self):
        pass

    def __arm_up_action(self):
        pass

    def get_name(self):
        return "PreserveAndExhibitStatuette"

    def get_points(self):
        return 32

    def required_delay(self):
        return 35

    def required_robots(self):
        return [1]
