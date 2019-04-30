from abc import abstractmethod
import time
import threading
import pymongo as pm
from pyftsm.ftsm import FTSM, FTSMStates, FTSMTransitions

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
                 robot_store_status_collection='status'):
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
        raise NotImplementedError('[{0}] The implementation of the "running" method is mandatory'.format(self.name))

    @abstractmethod
    def recovering(self):
        '''Abstract method for component recovery
        '''
        raise NotImplementedError('[{0}] The implementation of the "recovering" method is mandatory'.format(self.name))

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
                        if depend_comp not in self.depend_statuses[monitor_type]:
                            self.depend_statuses[monitor_type][depend_comp] = {}

                        component_name, monitor_name = monitor_specs.split('/')
                        status_doc = collection.find_one({'id': component_name})
                        for monitor_data in status_doc['monitor_status']:
                            if monitor_name != monitor_data['monitorName']:
                                continue

                            self.depend_statuses[monitor_type][depend_comp][monitor_specs] = \
                                monitor_data['healthStatus']
                return self.depend_statuses
            except pm.errors.OperationFailure as exc:
                print('[ftms_base] {0}'.format(exc))

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
