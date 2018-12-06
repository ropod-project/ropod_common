#include "ZyreBaseCommunicator.h"
#include <json/json.h>
#include <iostream>
#include <sstream>

class ZyreNode : public ZyreBaseCommunicator
{
    public:
    ZyreNode(const std::string &nodeName,
	    const std::vector<std::string> &groups,
	    const std::vector<std::string> &messageTypes,
	    const bool &printAllReceivedMessages,
        const std::string &interface="",
        bool acknowledge = false)
    : ZyreBaseCommunicator(nodeName, groups, messageTypes, printAllReceivedMessages, interface, acknowledge)
    {};

    private:
    virtual void recvMsgCallback(ZyreMsgContent* msgContent);
    virtual void sendMessageStatusCallback(const std::string &msgId, bool status);
};

void ZyreNode::recvMsgCallback(ZyreMsgContent* msgContent)
{
    //std::cout << this->getNodeName() << " received message" << "\n";
    //std::cout << message << "\n";
}

void ZyreNode::sendMessageStatusCallback(const std::string &msgId, bool status)
{
    std::cout << "Got send status for " << msgId << ": " << status << std::endl;
}

std::string getMessage(const std::string &message_type)
{
    Json::Value msg;
    msg["header"]["type"] = message_type;
    msg["header"]["metamodel"] = "ropod-msg-schema.json";
    zuuid_t * uuid = zuuid_new();
    const char * uuid_str = zuuid_str_canonical(uuid);
    msg["header"]["msgId"] = uuid_str;
    zuuid_destroy (&uuid);
    char *timestr = zclock_timestr (); // TODO: this is not ISO 8601
    msg["header"]["timestamp"] = timestr;
    zstr_free(&timestr);

    msg["payload"]["metamodel"] = "none";
    msg["payload"]["msg"] = "empty";

    std::stringstream jsonMsg("");
    jsonMsg << msg;
    return jsonMsg.str();
}

int main(int argc, char *argv[])
{
    std::vector<std::string> messageTypes;
    messageTypes.push_back("TASK");
    messageTypes.push_back("TASK-REQUEST");

    std::vector<std::string> acknowledgeMessageTypes;
    acknowledgeMessageTypes.push_back("TASK");
    acknowledgeMessageTypes.push_back("TASK-REQUEST");

    std::vector<std::string> groups;
    groups.push_back("group1");
    bool b = true;

    ZyreNode node_1("ZyreNode_test_1", groups, messageTypes, b, "", true);
    node_1.setExpectAcknowledgementFor(acknowledgeMessageTypes);
    node_1.setSendAcknowledgementFor(messageTypes);
    ZyreNode node_2("ZyreNode_test_2", groups, messageTypes, b, "", false);
    node_2.setExpectAcknowledgementFor(acknowledgeMessageTypes);
    node_2.setSendAcknowledgementFor(messageTypes);

    std::string msg1 = getMessage("TASK");
    std::string msg2 = getMessage("TASK-REQUEST");

    // shout a TASK message expecting an acknowledgement
    node_1.shout(msg1, "group1");
    // since node_2 does not acknowledge messages, node_1 will retry
    zclock_sleep(6000);

    // node_3 will now respond with an acknowledgement on the
    // next message received
    ZyreNode node_3("ZyreNode_test_3", groups, messageTypes, b, "", true);
    node_3.setExpectAcknowledgementFor(acknowledgeMessageTypes);
    node_3.setSendAcknowledgementFor(messageTypes);

    // once acknowledgement is received, node_1 stops resending stuff
    zclock_sleep(8000);

    return 0;
}
