#ifndef ZYREBASECOMMUNICATOR_H
#define ZYREBASECOMMUNICATOR_H

#include<zyre.h>
#include<string>
#include<vector>
#include <json/json.h>
#include <ctime>

struct ZyreParams
{
    std::string nodeName;
    std::vector<std::string> groups;
    std::vector<std::string> messageTypes;
};

struct Peer
{
    std::string name;
    std::string id;
    std::string address;
};

struct ZyreMsgContent
{
    std::string event;
    std::string peer;
    std::string name;
    std::string group;
    std::string message;
};

class ZyreBaseCommunicator {
    public:
    ZyreBaseCommunicator(const std::string &nodeName,
	    const std::vector<std::string> &groups,
	    const std::vector<std::string> &messageTypes,
	    const bool &printAllReceivedMessages,
        const std::string& interface="",
        bool acknowledge = false);
    ~ZyreBaseCommunicator();

    void shout(const std::string &message);
    void shout(const std::string &message, const std::string &group);
    void shout(const std::string &message, const std::vector<std::string> &groups);
    void whisper(const std::string &message, const std::string &id);
    void whisper(const std::string &message, const std::vector<std::string> &ids);
    void joinGroup(const std::string &group);
    void joinGroup(const std::vector<std::string> &groups);
    void leaveGroup(const std::string &group);
    void leaveGroup(std::vector<std::string> groups);

    std::string getNodeName() {return params.nodeName;}
    std::vector<std::string> getJoinedGroups() {return params.groups;}
    std::vector<std::string> getReceivingMessageTypes() {return params.messageTypes;}
    ZyreParams getZyreParams() {return params;}
    void printNodeName();
    void printJoinedGroups();
    void printReceivingMessageTypes();
    void printZyreMsgContent(const ZyreMsgContent &msgContent);
    std::string getTimeStamp();

    virtual void recvMsgCallback(ZyreMsgContent* msgContent) = 0;
    Json::Value convertZyreMsgToJson(ZyreMsgContent* msg_params);
    std::string convertJsonToString(const Json::Value &root);
    std::string generateUUID();

    private:
    ZyreParams params;
    zyre_t *node;
    zactor_t* receiveActor;
    zactor_t* discoverActor;
    bool printAllReceivedMessages;
    const int ZYRESLEEPTIME = 250;
    Json::StreamWriterBuilder json_stream_builder_;
    bool acknowledge;

    static void receiveLoop(zsock_t* pipe, void* args);
    static void discoverLoop(zsock_t* pipe, void* args);
    zmsg_t* stringToZmsg(std::string msg);
    ZyreMsgContent* zmsgToZyreMsgContent(zmsg_t *msg);
    void sendAcknowledgement(ZyreMsgContent * msgContent);
};

#endif
