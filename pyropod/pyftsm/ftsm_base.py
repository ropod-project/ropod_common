from pyftsm.ftsm import FTSM, FTSMStates, FTSMTransitions

class FTSMBase(FTSM):
    '''ROPOD-specific implementation of a fault-tolerant state machine

    @author Alex Mitrevski
    @maintainer Alex Mitrevski, Santosh Thoduka, Argentina Ortega Sainz
    @contact aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de, argentina.ortega@h-brs.de
    '''
    def __init__(self, name, dependencies, max_recovery_attempts=1):
        super(FTSMBase, self).__init__(name, dependencies, max_recovery_attempts)

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

    def running(self):
        '''Abstract method for the behaviour of a component during active operation
        '''
        pass

    def recovering(self):
        '''Abstract method for component recovery
        '''
        pass
