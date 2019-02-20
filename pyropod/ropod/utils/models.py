from ropod.utils.timestamp import TimeStamp as ts
from ropod.utils.uuid import generate_uuid
from ropod.structs.task import Task, TaskRequest
from ropod.structs.elevator import ElevatorRequest, RobotCallUpdate, RobotElevatorCallReply

meta_model_template = 'ropod-%s-schema.json'


class MessageFactory(object):

    def create_message(self, contents, recipients=None):
        if isinstance(contents, Task):
            model = 'TASK'
        elif isinstance(contents, TaskRequest):
            model = 'TASK-REQUEST'
        elif isinstance(contents, ElevatorRequest):
            model = 'ELEVATOR-CMD'
        elif isinstance(contents, RobotCallUpdate):
            model = 'ROBOT-CALL-UPDATE'
        elif isinstance(contents, RobotElevatorCallReply):
            model = 'ROBOT-ELEVATOR-CALL-REPLY'

        msg = self.get_header(model, recipients=recipients)
        payload = self.get_payload(contents, model.lower())
        msg.update(payload)
        return msg

    @staticmethod
    def get_header(message_type, meta_model='msg', recipients=None):
        if recipients is not None and not isinstance(recipients, list):
            raise Exception("Recipients must be a list of strings")

        return {"header": {'type': message_type,
                           'metamodel': 'ropod-%s-schema.json' % meta_model,
                           'msgId': generate_uuid(),
                           'timestamp': ts.get_time_stamp(),
                           'receiverIds': recipients}}

    @staticmethod
    def get_payload(contents, model):
        payload = contents.to_dict()
        metamodel = meta_model_template % model
        payload.update(metamodel=metamodel)
        return {"payload": payload}

    @staticmethod
    def update_timestamp(message):
        header = message.get('header')
        if header:
            header.update(timeStamp=ts.get_time_stamp())
        else:
            header = MessageFactory.get_header(None)
            message.update(header)

    @staticmethod
    def update_msg_id(message, id=None):
        header = message.get('header')

        if header:
            if id:
                header.update(msgId=id)
            else:
                header.update(msgId=generate_uuid())
        else:
            header = MessageFactory.get_header(None)
            message.update(header)
