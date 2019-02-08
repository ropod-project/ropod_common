from ropod.structs.area import Area
from ropod.structs.action import Action
from ropod.structs.status import TaskStatus


class RobotTask(object):
    def __init__(self):
        self.earliest_start_time = -1.
        self.latest_start_time = -1.
        self.estimated_end_time = -1.
        self.priority = 0


class TaskRequest(object):
    def __init__(self):
        self.pickup_pose = Area()
        self.delivery_pose = Area()
        self.earliest_start_time = -1.
        self.latest_start_time = -2.
        self.user_id = ''
        self.cart_type = ''
        self.cart_id = ''
        self.priority = -1

    def to_dict(self):
        request_dict = dict()
        request_dict['pickup_pose'] = self.pickup_pose.to_dict()
        request_dict['delivery_pose'] = self.delivery_pose.to_dict()
        request_dict['earliest_start_time'] = self.earliest_start_time
        request_dict['latest_start_time'] = self.latest_start_time
        request_dict['user_id'] = self.user_id
        request_dict['cart_type'] = self.cart_type
        request_dict['cart_id'] = self.cart_id
        request_dict['priority'] = self.priority
        return request_dict

    @staticmethod
    def from_dict(request_dict):

        request = TaskRequest()
        request.user_id = request_dict["payload"]["userId"]
        request.cart_type = request_dict["payload"]["deviceType"]
        request.cart_id = request_dict["payload"]["deviceId"]
        request.earliest_start_time = request_dict["payload"]["earliestStartTime"]
        request.latest_start_time = request_dict["payload"]["latestStartTime"]

        request.pickup_pose = request_dict["payload"]["pickupLocation"]
        request.pickup_pose.floor_number = request_dict["payload"]["pickupLocationLevel"]

        request.delivery_pose = request_dict["payload"]["deliveryLocation"]
        request.delivery_pose.floor_number = request_dict["payload"]["deliveryLocationLevel"]
        request.priority = request_dict["payload"]["priority"]
        return request


class Task(object):
    EMERGENCY = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

    def __init__(self, id='', robot_actions=dict(), deviceType='', deviceId='', team_robot_ids=list(),
                 earliest_start_time=-1, latest_start_time=-1, estimated_duration=-1, start_time=-1,
                 finish_time=-1, pickup_pose=Area(), delivery_pose=Area(), status=TaskStatus(), priority=NORMAL):
        self.id = id
        self.robot_actions = robot_actions
        self.deviceType = deviceType
        self.deviceId = deviceId
        self.team_robot_ids = team_robot_ids
        self.earliest_start_time = earliest_start_time
        self.latest_start_time = latest_start_time
        self.estimated_duration = estimated_duration
        self.start_time = start_time
        self.finish_time = finish_time

        if isinstance(pickup_pose, Area):
            self.pickup_pose = pickup_pose
        else:
            raise Exception('pickup_pose must be an object of type Area')

        if isinstance(delivery_pose, Area):
            self.delivery_pose = delivery_pose
        else:
            raise Exception('delivery_pose must be an object of type Area')

        if isinstance(status, TaskStatus):
            self.status = status
        else:
            raise Exception("status must be an object of TaskStatus type")

        if priority in (self.EMERGENCY, self.NORMAL, self.HIGH, self.LOW):
            self.priority = priority
        else:
            raise Exception("Priority must have one of the following values:\n"
                            "0) Urgent\n"
                            "1) High\n"
                            "2) Normal\n"
                            "3) Low")

    def to_dict(self):
        task_dict = dict()
        task_dict['id'] = self.id
        task_dict['deviceType'] = self.deviceType
        task_dict['deviceId'] = self.deviceId
        task_dict['team_robot_ids'] = self.team_robot_ids
        task_dict['earliest_start_time'] = self.earliest_start_time
        task_dict['latest_start_time'] = self.latest_start_time
        task_dict['estimated_duration'] = self.estimated_duration
        task_dict['start_time'] = self.start_time
        task_dict['finish_time'] = self.finish_time
        task_dict['pickup_pose'] = self.pickup_pose.to_dict()
        task_dict['delivery_pose'] = self.delivery_pose.to_dict()
        task_dict['priority'] = self.priority
        task_dict['status'] = self.status.to_dict()
        task_dict['robot_actions'] = dict()
        for robot_id, actions in self.robot_actions.items():
            task_dict['robot_actions'][robot_id] = list()
            for action in actions:
                action_dict = Action.to_dict(action)
                task_dict['robot_actions'][robot_id].append(action_dict)
        return task_dict

    @staticmethod
    def from_dict(task_dict):
        task = Task()
        task.id = task_dict['id']
        task.deviceType = task_dict['deviceType']
        task.deviceId = task_dict['deviceId']
        task.team_robot_ids = task_dict['team_robot_ids']
        task.earliest_start_time = task_dict['earliest_start_time']
        task.latest_start_time = task_dict['latest_start_time']
        task.estimated_duration = task_dict['estimated_duration']
        task.start_time = task_dict['start_time']
        task.finish_time = task_dict['finish_time']
        task.pickup_pose = Area.from_dict(task_dict['pickup_pose'])
        task.delivery_pose = Area.from_dict(task_dict['delivery_pose'])
        task.priority = task_dict['priority']
        task.status = TaskStatus.from_dict(task_dict['status'])
        for robot_id, actions in task_dict['robot_actions'].items():
            task.robot_actions[robot_id] = list()
            for action_dict in actions:
                action = Action.from_dict(action_dict)
                task.robot_actions[robot_id].append(action)
        return task
