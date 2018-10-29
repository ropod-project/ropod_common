class ZyreParams(object):
    def __init__(self, node_name=None, groups=None, message_types=None):
        self.node_name = node_name
        self.groups = groups
        self.message_types = message_types

    def __str__(self):
        return str(self.node_name), str(self.groups), str(self.message_types)


class ZyreMsg(object):
    def __init__(self, **kwds):
        self.msg_type = None
        self.peer_uuid = None
        self.peer_name = None
        self.headers = None
        self.msg_content = None
        self.group_name = None
        self.__dict__.update(kwds)

    def update(self, **kwds):
        self.__dict__.update(kwds)

    def __str__(self):
        return '''Type: {}
Peer UUID: {}
Peer Name: {}
Headers: {}
Content: {}
Group: {}'''.format(self.msg_type, self.peer_uuid, self.peer_name, self.headers, self.msg_content, self.group_name)