#include "ftsm_base.h"

namespace ftsm
{
    FTSMBase::FTSMBase(std::string name, std::vector<std::string> dependencies, int max_recovery_attempts)
     : FTSM(name, dependencies, max_recovery_attempts) { }

    std::string FTSMBase::init()
    {
        return ftsm::FTSMTransitions::INITIALISED;
    }

    std::string FTSMBase::configuring()
    {
        return ftsm::FTSMTransitions::DONE_CONFIGURING;
    }

    std::string FTSMBase::ready()
    {
        return ftsm::FTSMTransitions::RUN;
    }
}
