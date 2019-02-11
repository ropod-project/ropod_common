from ropod.utils.timestamp import TimeStamp as ts
from ropod.utils.uuid import generate_uuid
from ropod.structs.task import Task, TaskRequest
from ropod.structs.elevator import ElevatorRequest

meta_model_template = 'ropod-%s-schema.json'


class MessageFactory(object):
    def __init__(self):
        self.hf = HeaderFactory()
        self.pf = PayloadFactory()

    def create_message(self, contents, recipients=None):
        if isinstance(contents, Task):
            model = 'TASK'
        elif isinstance(contents, TaskRequest):
            model = 'TASK-REQUEST'
        elif isinstance(contents, ElevatorRequest):
            model = 'ELEVATOR-CMD'

        msg = self.hf.get_header(model, recipients=recipients)
        payload = self.pf.get_payload(contents, model.lower())
        msg.update(payload)
        return msg


class HeaderFactory(object):

    @staticmethod
    def get_header(message_type, meta_model='msg', recipients=None):
        if recipients is not None and not isinstance(recipients, list):
            raise Exception("Recipients must be a list of strings")

        return {"header": {'type': message_type,
                           'metamodel': 'ropod-%s-schema.json' % meta_model,
                           'msgId': generate_uuid(),
                           'timeStamp': ts.get_time_stamp(),
                           'recipients': recipients}}


class PayloadFactory(object):

    @staticmethod
    def get_payload(contents, model):
        payload = contents.to_dict()
        metamodel = meta_model_template % model
        payload.update(metamodel=metamodel)
        return {"payload": payload}
