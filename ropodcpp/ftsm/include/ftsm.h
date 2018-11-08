#include "ftsm_base.h"

namespace ftsm
{
    class FTSM : public FTSMBase
    {
    public:
        FTSM(std::string name, std::vector<std::string> dependencies, int max_recovery_attempts=1);

        /**
         * Method for component initialisation
         */
        virtual std::string init();

        /**
         * Method for component configuration/reconfiguration
         */
        virtual std::string configuring();

        /**
         * Method for the behaviour of a component when it is ready for operation, but not active
         */
        virtual std::string ready();

        /**
         * Abstract method for the behaviour of a component during active operation
         */
        virtual std::string running() = 0;

        /**
         * Abstract method for component recovery
         */
        virtual std::string recovering() = 0;
    };
}
