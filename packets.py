import time
import json
from models import Server, User

class EuphoriaPacket(object):
    def __init__(self, message):
        if type(message) is str:
            message = json.loads(message)
        if 'id' in message and 'type' in message:
            self.packet_id = message['id']
            self.packet_type = message['type']

class EuphoriaMessage(EuphoriaPacket):
    def __init__(self, message):
        super(EuphoriaMessage, self).__init__(message)
        if 'data' in message:
            message = message['data']
        self.message_id = message['id']
        self.timestamp = message['time']
        self.sender = User.create(message['sender'])
        self.parent = message['parent']
        self.content = message['content']

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def is_emote(self):
        return self.content.find('/me') == 0

    def urwid_string(self, depth, index=None):
        local_time = time.localtime(self.timestamp)
        index_str = ''
        if index:
            index_str = '[{}]'.format(index)
        if self.is_emote():
            return '{}{}| {}<{}{}>'.format(
                index_str,
                time.strftime("%H:%M:%S", local_time),
                '| '*depth,
                self.sender.name,
                self.content.replace('/me', ''))
        else:
            return '{}{}| {}{}: {}'.format(
                index_str,
                time.strftime("%H:%M:%S", local_time),
                '| '*depth,
                self.sender,
                self.content)

    def __str__(self):
        local_time = time.localtime(self.timestamp)
        return '{}|{}: {}'.format(
            time.strftime("%H:%M:%S", local_time),
            self.sender,
            self.content)

    def __eq__(self, other):
        attrs = ['message_id', 'timestamp', 'sender', 'parent', 'content']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.message_id == other.message_id \
               and self.timestamp == other.timestamp \
               and self.sender == other.sender \
               and self.parent == other.parent \
               and self.content == other.content

class EuphoriaNickChange(EuphoriaPacket):
    pass

class EuphoriaPing(EuphoriaPacket):
    def __init__(self, message):
        super(EuphoriaPing, self).__init__(message)
        if 'data' in message:
            message = message['data']
        self.sent_time = message['time']
        self.next_time = message['next']

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'ping[{}]->{}'.format(self.sent_time, self.next_time)

    def __eq__(self, other):
        attrs = ['sent_time', 'next_time']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.sent_time == other.sent_time \
               and self.next_time == other.next_time

class EuphoriaSnapshot(EuphoriaPacket):
    def __init__(self, message):
        super(EuphoriaSnapshot, self).__init__(message)
        if 'data' in message:
            message = message['data']
        self.version = message['version']
        self.session_id = message['session_id']
        self.log = message['log']
        self.listing = message['listing']        
        self._users = None
        self._messages = None

    @property
    def users(self):
        if not self._users:
            self._users = []
            for user in self.listing:
                self._users.append(EuphoriaUser.create(user))
        return self._users

    @property
    def messages(self):
        if not self._messages:
            self._messages = []
            for message in self.log:
                self._messages.append(EuphoriaMessage.create(message))
        return self._users

def get_message_object(message):
    type_to_class_map = {
        'ping-event': EuphoriaPing,
        'snapshot-event': EuphoriaSnapshot,
        'send-event': EuphoriaMessage,
        'send-reply': EuphoriaMessage, # do something about this?
        'part-event': None
    }

    if type(message) is not dict:
        message = json.loads(message)

    print('message: {}'.format(message))
    if 'type' in message:
        if message['type'] in type_to_class_map:
            type_class = type_to_class_map[message['type']]
            if type_class:
                return type_class(message)

    else:
        if 'id' in message and 'name' in message:
            return User.create(message)

    return None
