from ropod.utils.timestamp import TimeStamp as ts
from ropod.utils.uuid import generate_uuid

meta_model_template = 'ropod-%s-schema.json'


class MessageFactory(object):
    pass


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
    def task_payload(task):
        payload = task.to_dict()
        metamodel = meta_model_template % "task"
        payload.update(metamodel=metamodel)
        return {"payload": payload}
