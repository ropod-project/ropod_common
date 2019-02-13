import time
import uuid
import json
import zmq
import ast
import logging
from datetime import timedelta, datetime
from ropod.utils.timestamp import TimeStamp as ts
from ropod.utils.uuid import generate_uuid

from pyre_base.zyre_params import ZyreMsg
from pyre_base.base_class import PyreBase

ZYRE_SLEEP_TIME = 0.250  # type: float


class RopodPyre(PyreBase):
    def __init__(self, node_name, groups, message_types, verbose=False,
                 interface=None, acknowledge=True, ropod_uuid=None, extra_headers={},
                 retries=5):
        """

        :param node_name: a string containing the name of the node
        :param groups: a list of strings containing the groups the node will join
        :param message_types: a list of strings containing the message types to acknowledge
        :param verbose: boolean indicating whether to print output to the terminal
        :param interface: sets the interface to be used by the node
        :param acknowledge: boolean indicating whether the node should send acknowledgements for
                            shout and whispered messages
        :param ropod_uuid: a string containing the hexadecimal version of a nodes uuid
        :param extra_headers: a dictionary containing the additional headers
        """
        self.logger = logging.getLogger('RopodPyre')

        self.acknowledge = acknowledge
        self.unacknowledged_msgs = {}
        self.number_of_retries = retries

        if self.acknowledge:
            self.unacknowledged_msgs = {}
            self.number_of_retries = retries

        super(RopodPyre, self).__init__(node_name, groups, message_types,
                                        verbose=verbose, interface=interface)

        self.set_header('name', node_name)
        if ropod_uuid:
            self.set_header('uuid', ropod_uuid)
        else:
            self.set_header('uuid', str(self.uuid()))

        if extra_headers:
            for key in extra_headers:
                self.set_header(key, extra_headers[key])

        self.logger.info('Initialized %s', self.name())

    def receive_msg_cb(self, msg_content):
        pass

    def convert_zyre_msg_to_dict(self, msg):
        try:
            return ast.literal_eval(msg)
        except ValueError:
            try:
                return json.loads(msg)
            except Exception as e:
                print("Couldn't convert zyre_msg to dictionary")
                print(e)
                return None

    def receive_loop(self, ctx, pipe):

        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        poller.register(self.socket(), zmq.POLLIN)

        while not self.terminated:
            try:
                # Call the poller with a timeout of 1000 ms.
                # If a timeout occurs, items is empty, so we just check if we need to resend any messages.
                # This makes sure we check resending of messages at least every second.
                # Otherwise we're dependent on receiving a message to get out of the polling call.
                # If items is not empty, it means we've received a message on one of the pipes,
                #  so we parse the message etc.
                items = dict(poller.poll(1000))
                if not items and self.acknowledge:
                    self.resend_message_cb()
                elif pipe in items and items[pipe] == zmq.POLLIN:
                    message = pipe.recv()
                    if message.decode('utf-8') == "$$STOP":
                        break
                    print("CHAT_TASK: %s" % message)
                else:
                    self.received_msg = self.recv()

                    zyre_msg = self.get_zyre_msg()

                    if zyre_msg.msg_type in ('LEAVE', 'EXIT'):
                        continue
                    elif zyre_msg.msg_type == "STOP":
                        break
                    elif zyre_msg.msg_type not in ('WHISPER', 'JOIN', 'PING', 'PING_OK', 'HELLO', 'ENTER'):
                        self.logger.warning("Unrecognized message type: %s", zyre_msg.msg_type)

                    if zyre_msg.msg_type in ("SHOUT", "WHISPER") and self.acknowledge:
                            self.send_acknowledgment(zyre_msg)
                            self.check_unacknowledged_msgs(zyre_msg)

                    self.zyre_event_cb(zyre_msg)

            except (KeyboardInterrupt, SystemExit):
                self.terminated = True
                break
        print("Exiting.......")

    def zyre_event_cb(self, zyre_msg):
        if zyre_msg.msg_type in ("SHOUT", "WHISPER"):
            self.receive_msg_cb(zyre_msg.msg_content)

    def shout(self, msg, groups=None):
        """
        Shouts a message to a given group.
        For Python 3 encodes the string to utf-8

        Params:
            msg: the string to be sent
            groups: can be a string with the name of the group, or a list of
                    strings
        """

        if isinstance(msg, dict):
            # NOTE: json.dumps must be used instead of str, since it returns
            # the correct type of string
            if self.acknowledge:
                self.check_msg_retries(msg, "SHOUT", groups=groups)
            message = json.dumps(msg, default=str).encode('utf-8')
        else:
            message = msg.encode('utf-8')

        if groups:
            if isinstance(groups, list):
                for group in groups:
                    super(PyreBase, self).shout(group, message)
                    time.sleep(ZYRE_SLEEP_TIME)
            else:
                # TODO Do we need formatted strings?
                super(PyreBase, self).shout(groups, message)
        else:
            for group in self.groups():
                super(PyreBase, self).shout(group, message)

    def whisper(self, msg, peer=None, peers=None, peer_name=None, peer_names=None):
        """
        Whispers a message to a peer.
        For Python 3 encodes the message to utf-8.

        Params:
            :string msg: the string to be sent
            :UUID peer: a single peer UUID
            :list peers: a list of peer UUIDs
            :string peer_name the name of a peer
            :list peer_names a list of peer names
        """

        if isinstance(msg, dict):
            # NOTE: json.dumps must be used instead of str, since it returns
            # the correct type of string
            if self.acknowledge:
                self.check_msg_retries(msg, "WHISPER", peer=peer, peers=peers, peer_name=peer_name,
                                       peer_names=peer_names)

            message = json.dumps(msg, default=str).encode('utf-8')
        else:
            message = msg.encode('utf-8')

        if not peer and not peers and not peer_name and not peer_names:
            print("Need a peer to whisper to, doing nothing...")
            return

        if peer:
            super(PyreBase, self).whisper(peer, message)
        elif peers:
            for peer in peers:
                time.sleep(ZYRE_SLEEP_TIME)
                self.whispers(peer, message)
        elif peer_name:
            valid_uuids = [k for k, v in self.peer_directory.items() if v == peer_name]
            for peer_uuid in valid_uuids:
                time.sleep(ZYRE_SLEEP_TIME)
                super(PyreBase, self).whisper(peer_uuid, message)
        elif peer_names:
            for peer_name in peer_names:
                valid_uuids = [k for k, v in self.peer_directory.items() if v == peer_name]
                for peer_uuid in valid_uuids:
                    super(PyreBase, self).whisper(peer_uuid, message)
                time.sleep(ZYRE_SLEEP_TIME)

    def send_acknowledgment(self, zyre_msg):
        """
        This is a ROPOD-specific function to send acknowledgements to shouted and whispered messages defined in the
        node's constructor.
        Note that this assumes that the messages being received are writen in json, according to ropod-models.

        :param zyre_msg: zyre_msg which contains the message type, peer, group, and contents
        """

        if zyre_msg.msg_type == "SHOUT" and zyre_msg.group_name in self.own_groups():
            acknowledge = True
        elif zyre_msg.msg_type == "WHISPER":
            acknowledge = True
        else:
            acknowledge = False

        if zyre_msg.msg_content:
            try:
                contents = json.loads(zyre_msg.msg_content)
            except ValueError as e:
                print("Message is not formatted in json")
                return

            ropod_msg_type = contents["header"]["type"]
            if not acknowledge:
                return
            elif ropod_msg_type in self.message_types:
                # don't acknowledge if receiverIds are specified and this node is not one of them
                if 'receiverIds' in contents['header'].keys():
                    if self.name() not in contents['header']['receiverIds']:
                        return
                ack_msg = dict()
                header = dict()
                payload = dict()

                header["type"] = "ACKNOWLEDGEMENT"
                header["msgId"] = generate_uuid()

                payload["receivedMsg"] = contents["header"]["msgId"]

                ack_msg["header"] = header
                ack_msg["payload"] = payload

                self.whisper(ack_msg, zyre_msg.peer_uuid)

            elif ropod_msg_type in self.message_types and zyre_msg.msg_type == "WHISPER":
                print('Whispered message is not on the message type list; not sending acknowledgement...')
            else:
                return

    def check_msg_retries(self, message, zyre_msg_type, **kwargs):
        msg_type = message['header']['type']
        if msg_type not in self.message_types:
            return
        msg_id = message['header']['msgId']
        queued_msg = self.unacknowledged_msgs.get(msg_id, None)
        if queued_msg:
            retry = queued_msg.get('retry_number', 0)
            self.unacknowledged_msgs[msg_id]['retry_number'] = retry + 1
            self.unacknowledged_msgs[msg_id]['last_retry'] = self.unacknowledged_msgs[msg_id]['next_retry']

        else:
            self.unacknowledged_msgs[msg_id] = dict()
            self.unacknowledged_msgs[msg_id]['retry_number'] = 0
            current_ts = ts.get_time_stamp()
            self.unacknowledged_msgs[msg_id]['first_attempt'] = current_ts
            self.unacknowledged_msgs[msg_id]['last_retry'] = current_ts
            self.unacknowledged_msgs[msg_id]['zyre_msg_type'] = zyre_msg_type
            if 'receiverIds' in message['header'].keys():
                self.unacknowledged_msgs[msg_id]['receiverIds'] = message['header']['receiverIds']
            else:
                self.unacknowledged_msgs[msg_id]['receiverIds'] = list()
            self.unacknowledged_msgs[msg_id]['msg_args'] = dict()
            self.unacknowledged_msgs[msg_id]['msg_args']['msg'] = message
            self.unacknowledged_msgs[msg_id]['msg_args'].update(kwargs)
            deadline = timedelta(seconds=5 ** 5)
            self.unacknowledged_msgs[msg_id]['reply_by'] = ts.get_time_stamp(deadline)

        # TODO This needs to be probably adapted by message type
        next_attempt = timedelta(seconds=5)
        self.unacknowledged_msgs[msg_id]['next_retry'] = ts.get_time_stamp(next_attempt)
        print(self.unacknowledged_msgs[msg_id])

    def add_next_retry(self, msg_id):
        retry = self.unacknowledged_msgs[msg_id]['retry_number']
        timeout = 5 ** retry
        print(timeout, retry)
        next_attempt = timedelta(seconds=timeout)
        self.unacknowledged_msgs[msg_id]['last_retry'] = self.unacknowledged_msgs[msg_id]['next_retry']
        self.unacknowledged_msgs[msg_id]['next_retry'] = ts.get_time_stamp(next_attempt)
        self.unacknowledged_msgs[msg_id]['retry_number'] = retry + 1

    def check_unacknowledged_msgs(self, zyre_msg):
        if zyre_msg.msg_content:
            try:
                contents = json.loads(zyre_msg.msg_content)
            except ValueError as e:
                print("Message is not formatted in json", e)
                return

            ropod_msg_type = contents["header"]["type"]

        if ropod_msg_type == "ACKNOWLEDGEMENT":
            msg_id = contents["payload"]["receivedMsg"]
            print("Received acknowledgement from %s for %s!" % (zyre_msg.peer_name, msg_id))

            if msg_id in self.unacknowledged_msgs:
                # if no receiverIds were specified, accept any acknowledgement
                if not self.unacknowledged_msgs[msg_id]['receiverIds']:
                    self.unacknowledged_msgs.pop(msg_id)
                else:
                    peer_name = zyre_msg.peer_name
                    if peer_name in self.unacknowledged_msgs[msg_id]['receiverIds']:
                        self.unacknowledged_msgs[msg_id]['receiverIds'].remove(peer_name)
                        # if all receiverIds have acknowledged
                        print(self.unacknowledged_msgs[msg_id])
                        if not self.unacknowledged_msgs[msg_id]['receiverIds']:
                            print("All receiverIds have acknowledged message %s" % msg_id)
                            self.unacknowledged_msgs.pop(msg_id)

    def resend_message_cb(self):
        """
        This is a ROPOD specific function
        :return:
        """
        dropped_msgs = []

        for msg_id, attempt_info in self.unacknowledged_msgs.items():
            if attempt_info['retry_number'] > self.number_of_retries:
                print("Retried {} times, stopping.".format(self.number_of_retries))
                dropped_msgs.append(msg_id)
            else:
                now = datetime.now().timestamp()
                if attempt_info['next_retry'] < now:
                    print(attempt_info)
                    msg_args = attempt_info['msg_args']
                    if attempt_info['zyre_msg_type'] == "SHOUT":
                        self.shout(**msg_args)
                    elif attempt_info['zyre_msg_type'] == "WHISPER":
                        self.whisper(**msg_args)
                    self.add_next_retry(msg_id)

        for msg in dropped_msgs:
            self.unacknowledged_msgs.pop(msg)

    def test(self):
        print(self.name())
        print(self.groups())
        print(self.peers())

        time.sleep(ZYRE_SLEEP_TIME)
        msg = {'header': {'type': 'TEST_MSG', 'msgId': generate_uuid()},
               'payload': {'msg': 'test'}}

        for group in self.own_groups():
            self.shout(msg, group)
            time.sleep(1)
        self.shout('hello')
        self.whisper(msg, peer_name="chat_tester")
        self.whisper(msg, peer_names=["chat_tester", "chat_tester"])


def main():
    test = RopodPyre('test',
                     ["OTHER-GROUP", "CHAT", "TEST", "PYRE"],
                     ["TEST_MSG"],
                     True, acknowledge=True)

    try:
        test.start()
        test.test()
        while True:
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        test.shutdown()


if __name__ == '__main__':
    main()
