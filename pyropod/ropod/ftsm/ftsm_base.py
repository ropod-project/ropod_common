from abc import abstractmethod
import time
import threading
import pymongo as pm
from pyftsm.ftsm import FTSM, FTSMStates, FTSMTransitions

class DependMonitorTypes(object):
    HEARTBEAT = 'heartbeat'
    FUNCTIONAL = 'functional'

class MonitorConstants(object):
    NONE = 'none'

class FTSMBase(FTSM):
    '''ROPOD-specific implementation of a fault-tolerant state machine.

    @author Alex Mitrevski
    @maintainer Alex Mitrevski, Santosh Thoduka, Argentina Ortega Sainz
    @contact aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de, argentina.ortega@h-brs.de
    '''
    def __init__(self, name, dependencies=None,
                 dependency_monitors=None,
                 max_recovery_attempts=1,
                 robot_store_db_name='robot_store',
                 robot_store_db_port=27017,
                 robot_store_component_collection='components',
                 robot_store_status_collection='status',
                 robot_store_sm_state_collection='component_sm_states'):
        if not dependencies:
            dependencies = []

        if not dependency_monitors:
            dependency_monitors = {}

        super(FTSMBase, self).__init__(name, dependencies, max_recovery_attempts)
        self.dependency_monitors = dependency_monitors

        self.db_name = robot_store_db_name
        self.db_port = robot_store_db_port
        self.component_collection_name = robot_store_component_collection
        self.status_collection_name = robot_store_status_collection
        self.sm_state_collection_name = robot_store_sm_state_collection

        # we check whether the dependencies match the dependencies in the specification
        # and raise an AssertionError if they don't
        spec_dependencies = self.__get_component_dependencies(name)
        if self.dependencies != spec_dependencies:
            raise AssertionError('''[{0}] The component dependencies do not match the
                                 dependencies in the specification; expected {1}''' \
                                 .format(self.name, spec_dependencies))

        # we check whether the dependency monitors match the ones in the specification
        # and raise an AssertionError if they don't
        spec_dependency_monitors = self.__get_dependency_monitors(name)
        if self.dependency_monitors != spec_dependency_monitors:
            raise AssertionError('''[{0}] The dependency monitors do not match the
                                 monitors in the specification; expected {1}''' \
                                 .format(self.name, spec_dependency_monitors))

        self.depend_statuses = {}
        self.depend_status_thread = threading.Thread(target=self.get_dependency_statuses)
        self.depend_status_thread.daemon = True
        self.depend_status_thread.start()

        self.sm_state_thread = threading.Thread(target=self.write_sm_state)
        self.sm_state_thread.daemon = True
        self.sm_state_thread.start()

    def init(self):
        '''Method for component initialisation; returns FTSMTransitions.INITIALISED by default
        '''
        return FTSMTransitions.INITIALISED

    def configuring(self):
        '''Method for component configuration/reconfiguration;
        returns FTSMTransitions.DONE_CONFIGURING by default
        '''
        return FTSMTransitions.DONE_CONFIGURING

    def ready(self):
        '''Method for the behaviour of a component when it is ready
        for operation, but not active; returns FTSMTransitions.RUN by default
        '''
        return FTSMTransitions.RUN

    @abstractmethod
    def running(self):
        '''Abstract method for the behaviour of a component during active operation
        '''
        raise NotImplementedError('''[{0}] The implementation of the "running"
                                  method is mandatory'''.format(self.name))

    @abstractmethod
    def recovering(self):
        '''Abstract method for component recovery
        '''
        raise NotImplementedError('''[{0}] The implementation of the "recovering"
                                  method is mandatory'''.format(self.name))

    def process_depend_statuses(self):
        '''Processes the statuses of the component dependencies and returns
        a state transition string from FTSMTransitions (or None if no transition
        needs to take place.) The default implementation simply returns None.
        '''
        return None

    def setup_ros(self):
        '''For ROS components, performs any necessary setup steps (initialising
        a node, registering publishers/subscribers/services/action servers or clients).
        '''
        return None

    def tear_down_ros(self):
        '''For ROS components, performs any necessary cleanup steps when the ROS
        master dies so that the component can recover itself when the master
        comes back up (e.g. unregistering services).
        '''
        return None

    def get_dependency_statuses(self):
        '''Returns a dictionary representing the statuses
        of the components that the current component depends on,
        such that the dependencies are read from the robot store database.
        Since monitors can be of different types (e.g. existence, functional)
        the dictionary has the following format:

        {
            "type_1":
            {
                "monitor_name_1": {monitor-status-msg},
                ...,
                "monitor_name_n": {monitor-status-msg}
            },
            ...,
            "type_n":
            {
                "monitor_name_1": {monitor-status-msg},
                ...,
                "monitor_name_n": {monitor-status-msg}
            }
        }

        Throws a pm.errors.OperationFailure error in case of exceptions.

        Keyword arguments:
        component_name: str -- name of a component

        '''
        while not self.is_running:
            time.sleep(0.5)

        while self.current_state != FTSMStates.STOPPED and self.is_running:
            try:
                collection = self.__get_collection(self.status_collection_name)

                # we look for the statuses of all dependency monitors that we are interested in
                # and save them depending on the monitor type
                for monitor_type, monitors in self.dependency_monitors.items():
                    if monitor_type not in self.depend_statuses:
                        self.depend_statuses[monitor_type] = {}

                    for depend_comp, monitor_specs in monitors.items():
                        if monitor_specs == MonitorConstants.NONE:
                            continue

                        if depend_comp not in self.depend_statuses[monitor_type]:
                            self.depend_statuses[monitor_type][depend_comp] = {}

                        component_name, monitor_name = monitor_specs.split('/')
                        status_doc = collection.find_one({'component_id': component_name})
                        for monitor_data in status_doc['modes']:
                            if monitor_name != monitor_data['monitorName']:
                                continue

                            self.depend_statuses[monitor_type][depend_comp][monitor_specs] = \
                                monitor_data['healthStatus']
                time.sleep(0.5)
            except pm.errors.OperationFailure as exc:
                print('[ftms_base, get_dependency_statuses] {0}'.format(exc))

    def write_sm_state(self):
        while self.current_state != FTSMStates.STOPPED:
            try:
                collection = self.__get_collection(self.sm_state_collection_name)
                collection.replace_one({'component_name': self.name},
                                       {'component_name': self.name,
                                        'state': self.current_state},
                                       upsert=True)
                time.sleep(0.1)
            except pm.errors.OperationFailure as exc:
                print('[ftms_base, write_sm_state] {0}'.format(exc))

    def recover_from_possible_dead_rosmaster(self):
        '''For ROS components that have "roscore" listed as a **heartbeat** dependency,
        recovers from a dead ROS master in case the master is dead.
        self.tear_down_ros and self.setup_ros should be overridden for
        the recovery to be actually performed.
        '''
        if 'roscore' not in self.dependencies or DependMonitorTypes.HEARTBEAT not in self.depend_statuses:
            return

        master_available = self.depend_statuses[DependMonitorTypes.HEARTBEAT]\
                                               ['roscore']\
                                               ['ros/ros_master_monitor']\
                                               ['status']
        if master_available:
            return

        self.tear_down_ros()
        print('[{0}] Waiting for ROS master'.format(self.name))
        while not master_available:
            master_available = self.depend_statuses[DependMonitorTypes.HEARTBEAT]\
                                                   ['roscore']\
                                                   ['ros/ros_master_monitor']\
                                                   ['status']
            time.sleep(0.1)
        self.setup_ros()

    def __get_component_dependencies(self, component_name):
        '''Returns a list of components that the given component is dependent on,
        such that the dependencies are read from the robot store database.

        Throws a pm.errors.OperationFailure error in case of exceptions.

        Keyword arguments:
        component_name: str -- name of a component

        '''
        try:
            collection = self.__get_collection(self.component_collection_name)
            component_doc = collection.find_one({'component_name': component_name})

            dependencies = component_doc['dependencies']
            return dependencies
        except pm.errors.OperationFailure as exc:
            print('[ftms_base] {0}'.format(exc))
            raise

    def __get_dependency_monitors(self, component_name):
        '''Returns a nested dictionary in which the keys are names of
        components that "component_name" depends on and the values
        are dictionaries specifying the status monitors that are of interest
        to the current component. The dependencies are read
        from the robot store database.

        Throws a pm.errors.OperationFailure error in case of exceptions.

        Keyword arguments:
        component_name: str -- name of a component

        '''
        try:
            collection = self.__get_collection(self.component_collection_name)
            component_doc = collection.find_one({'component_name': component_name})

            dependency_monitors = component_doc['dependency_monitors']
            return dependency_monitors
        except pm.errors.OperationFailure as exc:
            print('[ftms_base] {0}'.format(exc))
            raise

    def __get_collection(self, collection_name):
        '''Returns a MongoDB collection with the given name
        from the "self.db" database.

        Keyword arguments:
        collection_name: str -- name of a MongoDB collection

        '''
        client = pm.MongoClient(port=self.db_port)
        db = client[self.db_name]
        collection = db[collection_name]
        return collection
