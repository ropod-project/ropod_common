from ropod.structs.status import RobotStatus

class Robot(object):
    def __init__(self):
        self.robot_id = ''
        self.schedule = ''
        self.status = RobotStatus()

    def to_dict(self):
        robot_dict = dict()
        robot_dict['robotId'] = self.robot_id
        robot_dict['schedule'] = self.schedule
        robot_dict['status'] = self.status.to_dict()
        return robot_dict

    @staticmethod
    def from_dict(robot_dict):
        robot = Robot()
        robot.robot_id = robot_dict['robotId']
        robot.schedule = robot_dict['schedule']
        robot.status = RobotStatus.from_dict(robot_dict['status'])
        return robot
