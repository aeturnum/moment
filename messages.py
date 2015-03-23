import time
import json

class EuphoriaServer(object):
    def __init__(self, id, era):
        self.id = id
        self.era = era
    def __eq__(self, other):
        if hasattr(other, 'era') and hasattr(other, 'id'):
            return self.id == other.id and self.era == other.era

class EuphoriaUser(object):
    def __init__(self, name, server_era, user_id, server_id):
        self.name = name
        self.id = user_id.split('-')[0]
        self.session = user_id.split('-')[1]
        self.server = EuphoriaServer(server_id, server_era)

    def __str__(self):
        return '[{}]'.format(self.name)

    @staticmethod
    def create(message):
        u = EuphoriaUser(
            message['name'],
            message['server_era'],
            message['id'],
            message['server_id'])
        return u

    def __eq__(self, other):
        attrs = ['name', 'id', 'session', 'server']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.name == other.name\
                and self.id == other.id \
                and self.session == other.session \
                and self.server == other.server

class EuphoriaMessage(object):
    def __init__(self, message_id, timestamp, sender, parent, content):
        self.id = message_id
        self.timestamp = int(timestamp)
        self.sender = sender
        self.parent = parent
        self.content = content

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

    @staticmethod
    def create(message):
        if 'data' in message:
            message = message['data']

        m = EuphoriaMessage(
                message['id'],
                message['time'],
                EuphoriaUser.create(message['sender']),
                message['parent'],
                message['content'])
        return m

    def __eq__(self, other):
        attrs = ['id', 'timestamp', 'sender', 'parent', 'content']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.id == other.id \
               and self.timestamp == other.timestamp \
               and self.sender == other.sender \
               and self.parent == other.parent \
               and self.content == other.content

class EuphoriaPing(object):
    def __init__(self, sent_time, next_ping):
        self.sent_time = sent_time
        self.next_time = next_ping

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'ping[{}]->{}'.format(self.sent_time, self.next_time)

    @staticmethod
    def create(message):
        if 'data' in message:
            message = message['data']
        p = EuphoriaPing(message['time'], message['next'])

        return p

    def __eq__(self, other):
        attrs = ['sent_time', 'next_time']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.sent_time == other.sent_time \
               and self.next_time == other.next_time

class EuphoriaSnapshot(object):
    def __init__(self, version, session_id, log, listing):
        self.version = version
        self.session_id = session_id
        self.log = log
        self.listing = listing
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

    @staticmethod
    def create(message):
        ss = EuphoriaSnapshot(
            message['data']['version'],
            message['data']['session_id'],
            message['data']['log'],
            message['data']['listing']),
        return ss

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
                return type_class.create(message)

    else:
        if 'id' in message and 'name' in message:
            return EuphoriaUser.create(message)

    return None
