import json
from models import Server, User, Message

class EuphoriaPacket(object):
    def __init__(self, packet):
        self._messages = []
        self._users = []
        if type(packet) is str:
            packet = json.loads(packet)
        if 'id' in packet and 'type' in packet:
            self.packet_id = packet['id']
            self.packet_type = packet['type']

    @property
    def messages(self):
        if hasattr(self, '_messages'):
            return self._messages

    @property
    def users(self):
        if hasattr(self, '_messages'):
            return self._users

class EuphoriaMessagePacket(EuphoriaPacket):
    def __init__(self, packet):
        super(EuphoriaMessage, self).__init__(packet)
        if 'data' in packet:
            packet = packet['data']
        self.messages = self.__parse_sub_message(self, packet)

    def __parse_sub_message(self, packet):
        return None

    @staticmethod
    def _parse_common_message(packet):
        return Message(packet['id'], 
                        packet['time'],
                        User.create(packet['sender']),
                        packet['parent'],
                        packet['content'])        

class EuphoriaSendEvent(EuphoriaMessagePacket):

    def __parse_sub_message(self, packet):
        return [EuphoriaMessagePacket._parse_common_message(packet)]

class EuphoriaReplyEvent(EuphoriaMessagePacket):

    def __parse_sub_message(self, packet):
        return [EuphoriaMessagePacket._parse_common_message(packet)]

class EuphoriaNickChange(EuphoriaPacket):
    pass

class EuphoriaPartEvent(EuphoriaPacket):
    pass

class EuphoriaJoinEvent(EuphoriaPacket):
    pass

class EuphoriaPing(EuphoriaPacket):
    def __init__(self, packet):
        super(EuphoriaPing, self).__init__(packet)
        if 'data' in packet:
            packet = packet['data']
        self.sent_time = packet['time']
        self.next_time = packet['next']

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
    def __init__(self, packet):
        super(EuphoriaSnapshot, self).__init__(packet)
        if 'data' in packet:
            packet = packet['data']
        self.version = packet['version']
        self.session_id = packet['session_id']
        self.log = packet['log']
        self.listing = packet['listing']        
        self._users = None
        self._messages = None

    @property
    def users(self):
        if not self._users:
            self._users = []
            for user in self.listing:
                self._users.append(User.create(user))
        return self._users

    @property
    def messages(self):
        if not self._messages:
            self._messages = []
            for message in self.log:
                self._messages.append(EuphoriaMessagePacket._parse_common_message(message))
        return self._messages

def parse_euphoria_packet(message):
    type_to_class_map = {
        'ping-event': EuphoriaPing,
        'ping-reply': None,
        'snapshot-event': EuphoriaSnapshot,
        'send-event': EuphoriaSendEvent,
        'send-reply': EuphoriaReplyEvent, # do something about this?
        'part-event': None,
        'join-event': None,
        'nick-event': EuphoriaNickChange
    }

    if type(message) is not dict:
        message = json.loads(message)

    if 'type' in message:
        if message['type'] in type_to_class_map:
            type_class = type_to_class_map[message['type']]
            if type_class:
                return type_class(message)

    else:
        if 'id' in message and 'name' in message:
            return User.create(message)

    return None
