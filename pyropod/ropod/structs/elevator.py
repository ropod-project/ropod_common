class ElevatorRequests(object):
    def __init__(self):
        self.current_floor = -1
        self.number_of_active_requests = -1


class ElevatorRequest(object):
    def __init__(self):
        self.elevator_id = -1
        self.operational_mode = ''
        self.start_floor = -1
        self.goal_floor = -1
        self.query_id = ''
        self.command = ''
        self.task_id = ''
        self.load = ''
        self.robot_id = ''
        self.status = ''

    def to_dict(self):
        request_dict = dict()
        request_dict['id'] = self.elevator_id
        request_dict['operationalMode'] = self.operational_mode
        request_dict['startFloor'] = self.start_floor
        request_dict['goalFloor'] = self.goal_floor
        request_dict['queryId'] = self.query_id
        request_dict['command'] = self.task_id
        request_dict['load'] = self.load
        request_dict['robotId'] = self.robot_id
        request_dict['status'] = self.status
        return request_dict

class Elevator(object):
    def __init__(self):
        self.elevator_id = -1
        self.floor = -1 # TODO: Need to match floors from toma messages to world model ones
        self.calls = -1
        self.is_available = False
        self.door_open_at_goal_floor = False
        self.door_open_at_start_floor = False

    def to_dict(self):
        elevator_dict = dict()
        elevator_dict['id'] = self.elevator_id
        elevator_dict['floor'] = self.floor
        elevator_dict['calls'] = self.calls
        elevator_dict['isAvailable'] = self.is_available
        elevator_dict['doorOpenAtGoalFloor'] = self.door_open_at_goal_floor
        elevator_dict['doorOpenAtStartFloor'] = self.door_open_at_start_floor
        return elevator_dict

    @staticmethod
    def from_dict(elevator_dict):
        elevator = Elevator()
        elevator.elevator_id = elevator_dict['id']
        elevator.floor = elevator_dict['floor']
        elevator.calls = elevator_dict['calls']
        elevator.is_available = elevator_dict['isAvailable']
        elevator.door_open_at_goal_floor = elevator_dict['doorOpenAtGoalFloor']
        elevator.door_open_at_start_floor = elevator_dict['doorOpenAtStartFloor']
        return elevator
