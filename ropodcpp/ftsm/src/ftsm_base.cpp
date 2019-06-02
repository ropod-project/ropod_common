#include "ftsm_base.h"

namespace
{
    std::string formatStrList(std::vector<std::string> strings)
    {
        std::string list_str = "[";
        for (unsigned int i=0; i < strings.size()-1; i++)
            list_str += strings[i] + ", ";
        list_str += strings[strings.size() - 1] + "]";
        return list_str;
    }

    std::string formatStrMap(std::map<std::string, std::map<std::string, std::string>> strings)
    {
        std::string map_str = "{\n";
        for (auto item : strings)
        {
            map_str += "  " + item.first + ":\n  {\n";
            for (auto monitors : item.second)
            {
                map_str += "    {" + monitors.first + ": " + monitors.second + " }\n";
            }
            map_str += "  }\n";
        }
        map_str += "}\n";
        return map_str;
    }
}

namespace ftsm
{
    std::string DependMonitorTypes::HEARTBEAT = "heartbeat";
    std::string DependMonitorTypes::FUNCTIONAL = "functional";

    FTSMBase::FTSMBase(const std::string &name, const std::vector<std::string> &dependencies,
                       const std::map<std::string, std::map<std::string, std::string>> &dependency_monitors,
                       int max_recovery_attempts,
                       std::string robot_store_db_name, int robot_store_db_port,
                       std::string robot_store_component_collection,
                       std::string robot_store_status_collection,
                       bool debug)
     : FTSM(name, dependencies, max_recovery_attempts), connection_{mongocxx::uri{}}
    {
        this->dependency_monitors = dependency_monitors;
        this->robot_store_db_name = robot_store_db_name;
        this->robot_store_db_port = robot_store_db_port;
        this->robot_store_component_collection = robot_store_component_collection;
        this->robot_store_status_collection = robot_store_status_collection;
        this->debug = debug;

        auto spec_dependencies = this->getComponentDependencies(name);
        if (this->dependencies != spec_dependencies)
        {
            std::string exc_msg = "[" + this->name + "] The component dependencies do not match" +
                                  " the dependencies in the specification; expected " +
                                  formatStrList(spec_dependencies);
            throw exc_msg;
        }

        auto spec_dependency_monitors = this->getDependencyMonitors(name);
        if (this->dependency_monitors != spec_dependency_monitors)
        {
            std::string exc_msg = "[" + this->name + "] The dependency monitors do not match" +
                                  " the monitors in the specification " +
                                  formatStrMap(spec_dependency_monitors);
            throw exc_msg;
        }

        for (auto monitor_data : this->dependency_monitors)
        {
            std::string monitor_type = monitor_data.first;
            std::map<std::string, std::string> monitors = monitor_data.second;
            this->depend_statuses[monitor_type] = std::map<std::string, std::map<std::string, std::string>>();
            for (auto monitor_desc : monitors)
            {
                std::string depend_comp = monitor_desc.first;
                std::string monitor_spec = monitor_desc.second;
                this->depend_statuses[monitor_type][depend_comp] = std::map<std::string, std::string>();
                this->depend_statuses[monitor_type][depend_comp][monitor_spec] = "";
            }
        }

        this->depend_status_thread = std::thread(&FTSMBase::getDependencyStatuses, this);
    }

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

    std::string FTSMBase::processDependStatuses()
    {
        return "";
    }

    std::vector<std::string> FTSMBase::getComponentDependencies(std::string component_name)
    {
        auto collection = connection_[this->robot_store_db_name]
                                     [this->robot_store_component_collection];
        auto component_doc = collection.find_one(bsoncxx::builder::stream::document{}
                                                 << "component_name" << component_name
                                                 << bsoncxx::builder::stream::finalize);
        auto document_view = (*component_doc).view();
        std::vector<std::string> dependencies;
        for (auto key : document_view)
        {
            std::string key_name = key.key().to_string();
            if (key_name == "dependencies")
            {
                auto dependency_array = document_view[key_name].get_array().value;
                for (auto dependency_elem : dependency_array)
                {
                    std::string dependency = bsoncxx::string::to_string(dependency_elem.get_utf8().value);
                    dependencies.push_back(dependency);
                }
            }
        }

        if (this->debug)
        {
            std::cout << component_name << " -- specification dependencies:" << std::endl;
            for (auto depend : dependencies)
            {
                std:: cout << depend << std::endl;
            }
            std::cout << std::endl;
        }
        return dependencies;
    }

    std::map<std::string, std::map<std::string, std::string>> FTSMBase::getDependencyMonitors(std::string component_name)
    {
        auto collection = connection_[this->robot_store_db_name]
                                     [this->robot_store_component_collection];
        auto component_doc = collection.find_one(bsoncxx::builder::stream::document{}
                                                 << "component_name" << component_name
                                                 << bsoncxx::builder::stream::finalize);
        std::map<std::string, std::map<std::string, std::string>> dependency_monitors;
        auto document_view = (*component_doc).view();
        for (auto key : document_view)
        {
            std::string key_name = key.key().to_string();
            if (key_name == "dependency_monitors")
            {
                auto dependency_type_elements = document_view[key_name].get_document().view();
                for (auto dependency_type_elem : dependency_type_elements)
                {
                    std::string dependency_type = dependency_type_elem.key().to_string();
                    if (dependency_monitors.count(dependency_type) == 0)
                    {
                        dependency_monitors[dependency_type] = std::map<std::string, std::string>();
                    }

                    auto dependency_elements = document_view[key_name][dependency_type].get_document().view();
                    for (auto dependency_elem : dependency_elements)
                    {
                        std::string dependency = dependency_elem.key().to_string();
                        std::string dependency_monitor = bsoncxx::string::to_string(dependency_elem.get_utf8().value);
                        dependency_monitors[dependency_type][dependency] = dependency_monitor;
                    }
                }
            }
        }

        if (this->debug)
        {
            std::cout << component_name << " -- dependency monitors:" << std::endl;
            for (auto map : dependency_monitors)
            {
                std::cout << map.first << std::endl;
                for (auto depend : map.second)
                {
                    std::cout << "    " << depend.first << ": " << depend.second << std::endl;
                }
                std::cout << std::endl;
            }
        }
        return dependency_monitors;
    }

    std::map<std::string, std::string> FTSMBase::getDependencyStatuses()
    {
        while (!this->is_running)
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }

        while (this->current_state != FTSMStates::STOPPED && this->is_running)
        {
            try
            {
                auto collection = connection_[this->robot_store_db_name]
                                             [this->robot_store_status_collection];

                for (auto monitor_data : this->dependency_monitors)
                {
                    std::string monitor_type = monitor_data.first;
                    std::map<std::string, std::string> monitors = monitor_data.second;

                    for (auto monitor_desc : monitors)
                    {
                        std::string depend_comp = monitor_desc.first;
                        std::string monitor_spec = monitor_desc.second;

                        int separator_idx = monitor_spec.find("/");
                        std::string component_name = monitor_spec.substr(0, separator_idx);
                        std::string monitor_name = monitor_spec.substr(separator_idx+1);

                        auto status_doc = collection.find_one(bsoncxx::builder::stream::document{}
                                                              << "id" << component_name
                                                              << bsoncxx::builder::stream::finalize);
                        auto document_view = (*status_doc).view();

                        for (auto monitor_data : document_view["monitor_status"].get_array().value)
                        {
                            std::string current_monitor_name = std::string(monitor_data["monitorName"].get_utf8().value);
                            if (monitor_name != current_monitor_name)
                                continue;

                            this->depend_statuses[monitor_type][depend_comp][monitor_spec] =
                                bsoncxx::to_json(monitor_data["healthStatus"].get_document().view());

                            if (this->debug)
                            {
                                std::cout << monitor_type << " -- " << depend_comp << " -- " << monitor_spec << std::endl;
                                std::cout << this->depend_statuses[monitor_type][depend_comp][monitor_spec] << std::endl;
                            }
                        }
                    }
                }
            }
            catch (std::exception& e)
            {
                std::cout << e.what() << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
    }
}
