import copy

from ropod.structs.action import Action
from ropod.structs.area import Area
from ropod.structs.status import TaskStatus
from ropod.utils.datasets import flatten_dict, keep_entry
from ropod.utils.uuid import generate_uuid
from ropod.utils.timestamp import TimeStamp


class RobotTask(object):
    def __init__(self):
        self.earliest_start_time = -1.
        self.latest_start_time = -1.
        self.estimated_end_time = -1.
        self.priority = 0


class TaskRequest(object):
    def __init__(self, id=''):
        if not id:
            self.id = generate_uuid()
        else:
            self.id = id
        self.pickup_pose = Area()
        self.delivery_pose = Area()
        self.earliest_start_time = -1.
        self.latest_start_time = -2.
        self.user_id = ''
        self.load_type = ''
        self.load_id = ''
        self.priority = -1

    def to_dict(self):
        request_dict = dict()
        request_dict['id'] = self.id
        request_dict['pickupLocation'] = self.pickup_pose.name
        request_dict['pickupLocationLevel'] = self.pickup_pose.floor_number
        request_dict['deliveryLocation'] = self.delivery_pose.name
        request_dict['deliveryLocationLevel'] = self.delivery_pose.floor_number
        request_dict['earliestStartTime'] = self.earliest_start_time
        request_dict['latestStartTime'] = self.latest_start_time
        request_dict['userId'] = self.user_id
        request_dict['loadType'] = self.load_type
        request_dict['loadId'] = self.load_id
        request_dict['priority'] = self.priority
        return request_dict

    @staticmethod
    def from_dict(request_dict):

        id = request_dict.get('id', generate_uuid())
        request = TaskRequest(id=id)

        request.load_type = request_dict["loadType"]
        request.load_id = request_dict["loadId"]
        request.user_id = request_dict["userId"]
        request.earliest_start_time = request_dict["earliestStartTime"]
        request.latest_start_time = request_dict["latestStartTime"]

        pickup_area_dict = request_dict.get('pickup_pose', None)
        if pickup_area_dict:
            request.pickup_pose = Area.from_dict(pickup_area_dict)
        else:# when the provided dict is from json schema
            request.pickup_pose = Area()
            request.pickup_pose.name = request_dict.get("pickupLocation", '')
            request.pickup_pose.floor_number = request_dict.get("pickupLocationLevel", 0)

        delivery_area_dict = request_dict.get('delivery_pose', None)
        if delivery_area_dict:
            request.delivery_pose = Area.from_dict(delivery_area_dict)
        else:# when the provided dict is from json schema
            request.delivery_pose = Area()
            request.delivery_pose.name = request_dict.get("deliveryLocation", '')
            request.delivery_pose.floor_number = request_dict.get("deliveryLocationLevel", 0)

        request.priority = request_dict["priority"]

        return request

    @staticmethod
    def to_csv(task_dict):
        """ Prepares dict to be written to a csv
        :return: dict
        """
        to_csv_dict = flatten_dict(task_dict)
        return to_csv_dict


class Task(object):
    """
    Parameters for task allocation:
    earliest_start_time: seconds (float)
    latest_start_time: seconds (float)
    start_pose_name: String indicating the location in the map where the task should start (taken from pickup_pose.name)
    finish_pose_name: String indicating the location in the map where the task should finish (taken from delivery_pose.name)
    """

    EMERGENCY = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

    def __init__(self, id='', robot_actions=dict(), loadType='', loadId='', team_robot_ids=list(),
                 earliest_start_time=-1, latest_start_time=-1, estimated_duration=-1, start_time=-1, finish_time=-1, pickup_pose=Area(), delivery_pose=Area(),
                 priority=NORMAL, pickup_start_time=-1, hard_constraints=True):

        if not id:
            self.id = generate_uuid()
        else:
            self.id = id
        self.robot_actions = robot_actions
        self.loadType = loadType
        self.loadId = loadId
        self.team_robot_ids = team_robot_ids
        self.earliest_start_time = earliest_start_time
        self.latest_start_time = latest_start_time
        self.estimated_duration = estimated_duration
        self.earliest_finish_time = earliest_start_time + estimated_duration
        self.latest_finish_time = latest_start_time + estimated_duration
        self.start_time = start_time
        self.finish_time = finish_time
        self.pickup_start_time = pickup_start_time
        self.hard_constraints = hard_constraints

        if isinstance(pickup_pose, Area):
            self.pickup_pose = pickup_pose
        else:
            raise Exception('pickup_pose must be an object of type Area')

        if isinstance(delivery_pose, Area):
            self.delivery_pose = delivery_pose
        else:
            raise Exception('delivery_pose must be an object of type Area')

        self.status = TaskStatus(self.id)

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
        task_dict['loadType'] = self.loadType
        task_dict['loadId'] = self.loadId
        task_dict['team_robot_ids'] = copy.copy(self.team_robot_ids)
        task_dict['earliest_start_time'] = self.earliest_start_time
        task_dict['latest_start_time'] = self.latest_start_time
        task_dict['estimated_duration'] = self.estimated_duration
        task_dict['earliest_finish_time'] = self.earliest_finish_time
        task_dict['latest_finish_time'] = self.latest_finish_time
        task_dict['start_time'] = self.start_time
        task_dict['finish_time'] = self.finish_time
        task_dict['pickup_pose'] = self.pickup_pose.to_dict()
        task_dict['delivery_pose'] = self.delivery_pose.to_dict()
        task_dict['priority'] = self.priority
        task_dict['status'] = self.status.to_dict()
        task_dict['pickup_start_time'] = self.pickup_start_time
        task_dict['hard_constraints'] = self.hard_constraints
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
        task.loadType = task_dict['loadType']
        task.loadId = task_dict['loadId']
        task.team_robot_ids = task_dict['team_robot_ids']
        task.earliest_start_time = task_dict['earliest_start_time']
        task.latest_start_time = task_dict['latest_start_time']
        task.estimated_duration = task_dict['estimated_duration']
        task.earliest_finish_time = task_dict['earliest_finish_time']
        task.latest_finish_time = task_dict['latest_finish_time']
        task.start_time = task_dict['start_time']
        task.finish_time = task_dict['finish_time']
        task.pickup_pose = Area.from_dict(task_dict['pickup_pose'])
        task.delivery_pose = Area.from_dict(task_dict['delivery_pose'])
        task.priority = task_dict['priority']
        task.status = TaskStatus.from_dict(task_dict['status'])
        task.pickup_start_time = task_dict['pickup_start_time']
        task.hard_constraints = task_dict['hard_constraints']
        for robot_id, actions in task_dict['robot_actions'].items():
            task.robot_actions[robot_id] = list()
            for action_dict in actions:
                action = Action.from_dict(action_dict)
                task.robot_actions[robot_id].append(action)
        return task

    @staticmethod
    def to_csv(task_dict):
        """ Prepares dict to be written to a csv
        :return: dict
        """
        flattened_dict = flatten_dict(task_dict)

        to_csv_dict = keep_entry(flattened_dict, 'pickup_pose', ['name'])
        to_csv_dict = keep_entry(to_csv_dict, 'delivery_pose', ['name'])
        to_csv_dict = keep_entry(to_csv_dict, 'status', ['status'])

        return to_csv_dict

    @staticmethod
    def from_request(request):
        task = Task()
        task.load_type = request.load_type
        task.load_id = request.load_id
        task.earliest_start_time = request.earliest_start_time
        task.latest_start_time = request.latest_start_time
        task.pickup_pose = request.pickup_pose
        task.delivery_pose = request.delivery_pose
        task.priority = request.priority
        task.status = TaskStatus(task.id)
        task.team_robot_ids = list()

        return task

    def update_earliest_and_latest_finish_time(self, estimated_duration):
        """ Updates the earliest and latest finish time of a task based on its estimated duration
        @param estimated duration: seconds (float)
        """
        self.earliest_finish_time = self.earliest_start_time + estimated_duration
        self.latest_finish_time = self.latest_start_time + estimated_duration

    def postpone_task(self, time):
        """ Postpones the task the time indicated in the time
        @param time: seconds (float)
        """
        self.earliest_start_time += time
        self.latest_start_time += time
        self.earliest_finish_time = self.earliest_start_time + self.estimated_duration
        self.latest_finish_time = self.latest_start_time + self.estimated_duration

    def update_task_estimated_duration(self, estimated_duration):
        """ Updates the estimated duration and the earliest and latest finish times
        @param estimated duration: seconds (float)
        """
        self.estimated_duration = estimated_duration
        self.update_earliest_and_latest_finish_time(estimated_duration)

    @property
    def start_pose_name(self):
        """ Returns the start_pose_name, used by the task allocator component

        The task_allocation component is expecting the task struct to have a
        start_pose_name
        This function maps self.pickup_pose.name to start_pose_name and returns
        its value
        """
        return self.pickup_pose.name

    @property
    def finish_pose_name(self):
        """ Returns the finish_pose_name, used by the task allocator component

       The task_allocation component is expecting the task struct to have a
       finish_pose_name
       This function maps self.delivery_pose.name to finish_pose_name and returns
       its value
        """
        return self.delivery_pose.name

    def set_status(self, status, **kwargs):
        self.status.status = status
        if status == TaskStatus.ONGOING:
            task = kwargs.get('task')
            self.status.estimated_task_duration = task.estimated_duration
            # TODO It may be better to wait for the robot to send it's current action
            # instead of setting it
            for robot_id in task.team_robot_ids:
                action = self.robot_actions[robot_id][0].id
                self.status.set_current_robot_action(robot_id, action)
                self.status.completed_robot_actions[robot_id] = list()

    def is_executable(self):
        """Returns True if the given task needs to be dispatched based on
         the task schedule; returns False otherwise
        """
        current_time = TimeStamp.get_time_stamp()
        if self.start_time < current_time:
            return True
        else:
            return False
