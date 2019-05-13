#include <chrono>
#include <thread>
#include <exception>
#include <bsoncxx/builder/stream/document.hpp>
#include <bsoncxx/json.hpp>
#include <bsoncxx/string/to_string.hpp>

#include <mongocxx/client.hpp>
#include <mongocxx/instance.hpp>

#include "ftsm.h"

namespace ftsm
{
    struct DependMonitorTypes
    {
        static std::string HEARTBEAT;
        static std::string FUNCTIONAL;
    };

    class FTSMBase : public FTSM
    {
    public:
        FTSMBase(std::string name, std::vector<std::string> dependencies,
                 std::map<std::string, std::map<std::string, std::string>> dependency_monitors={},
                 int max_recovery_attempts=1,
                 std::string robot_store_db_name="robot_store", int robot_store_db_port=27017,
                 std::string robot_store_component_collection="components",
                 std::string robot_store_status_collection="status",
                 bool debug=true);

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

    protected:
        std::map<std::string, std::map<std::string, std::string>> dependency_monitors;

        std::string robot_store_db_name;

        int robot_store_db_port;

        std::string robot_store_component_collection;

        std::string robot_store_status_collection;

        /*
        A dictionary of the form
        {
            component_monitor_type
            {
                component_name
                {
                    monitor: status
                }
            }
        }

        Example:
        {
            functional
            {
                smart_wheel
                {
                    ros/smart_wheel_ethercat_parser: [status-msg]
                }
            }
        }
         */
        std::map<std::string, std::map<std::string, std::map<std::string, std::string>>> depend_statuses;
    private:
        std::vector<std::string> getComponentDependencies(std::string component_name);

        std::map<std::string, std::map<std::string, std::string>> getDependencyMonitors(std::string component_name);

        std::map<std::string, std::string> getDependencyStatuses();

        std::thread depend_status_thread;

        bool debug;
    };
}
