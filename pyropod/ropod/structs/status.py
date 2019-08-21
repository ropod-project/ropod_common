import copy

from ropod.structs.area import Area
from ropod.utils.datasets import flatten_dict, keep_entry


class AvailabilityStatus:
    BUSY = 0  # Executing a task
    CHARGING = 1  # Recharging its battery
    IDLE = 2  # Available (no task assigned at the moment)
    FAILURE = 3  # Critical failure, robot can't recover
    DEFECTIVE = 4  # Robot has a failure, but still functional. Requires maintenance
    NO_COMMUNICATION = 5  # FMS has lost communication with the robot for more than 15 minutes?


class ComponentStatus:
    OPTIMAL: 1
    SUBOPTIMAL: 2
    DEGRADED: 3
    CRITICAL: 4
    FAILED: 5
    NONRESPONSIVE: -1


class TaskStatus(object):
    UNALLOCATED = 1
    ALLOCATED = 2
    SCHEDULED = 3  # Task is ready to be dispatched
    SHIPPED = 4  # The task was sent to the robot
    ONGOING = 5
    DELAYED = 6  # The robot is engaged in task execution but the task is taking longer than expected.
    COMPLETED = 7
    ABORTED = 8  # Aborted by the system, not by the user
    FAILED = 9   # Re-allocation or re-scheduling failed
    CANCELED = 10  # Canceled before execution starts
    PREEMPTED = 11  # Canceled during execution

    def __init__(self, task_id):
        self.task_id = task_id
        self.status = self.UNALLOCATED
        self.current_robot_action = dict()
        self.completed_robot_actions = dict()
        self.estimated_task_duration = -1.

    def to_dict(self):
        task_dict = dict()
        task_dict['task_id'] = self.task_id
        task_dict['status'] = self.status
        task_dict['estimated_task_duration'] = self.estimated_task_duration
        task_dict['current_robot_actions'] = copy.copy(self.current_robot_action)
        task_dict['completed_robot_actions'] = copy.copy(self.completed_robot_actions)
        return task_dict

    @staticmethod
    def from_dict(status_dict):
        status = TaskStatus(status_dict['task_id'])
        status.status = status_dict['status']
        status.estimated_task_duration = status_dict['estimated_task_duration']
        status.current_robot_action = status_dict['current_robot_actions']
        status.completed_robot_actions = status_dict['completed_robot_actions']
        return status

    @staticmethod
    def to_csv(status_dict):
        """ Prepares dict to be written to a csv
        :return: dict
        """
        # The dictionary is already flat and ready to be exported
        return status_dict

    def set_current_robot_action(self, robot_id, action):
        self.current_robot_action[robot_id] = action
