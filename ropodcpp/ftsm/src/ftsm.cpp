#include "ftsm.h"

namespace ftsm
{
    FTSM::FTSM(std::string name, std::vector<std::string> dependencies, int max_recovery_attempts)
     : FTSMBase(name, dependencies, max_recovery_attempts) { }

    std::string FTSM::init()
    {
        return ftsm::FTSMTransitions::INITIALISED;
    }

    std::string FTSM::configuring()
    {
        return ftsm::FTSMTransitions::DONE_CONFIGURING;
    }

    std::string FTSM::ready()
    {
        return ftsm::FTSMTransitions::RUN;
    }
}
