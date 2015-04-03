import time

class Server(object):
    def __init__(self, server_id, era):
        self.server_id = server_id
        self.era = era
    def __eq__(self, other):
        if hasattr(other, 'era') and hasattr(other, 'server_id'):
            return self.server_id == other.server_id and self.era == other.era

class User(object):
    def __init__(self, name, server_era, user_id, server_id):
        self.name = name
        self.user_id = user_id.split('-')[0]
        self.session = user_id.split('-')[1]
        self.server = Server(server_id, server_era)

    def __str__(self):
        return '[{}]'.format(self.name)

    @staticmethod
    def create(message):
        u = User(
            message['name'],
            message['server_era'],
            message['id'],
            message['server_id'])
        return u

    def __eq__(self, other):
        attrs = ['name', 'user_id', 'session', 'server']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.name == other.name\
                and self.user_id == other.user_id \
                and self.session == other.session \
                and self.server == other.server



class Message(object):
    def __init__(self, message_id, timestamp, sender, parent_id, content):
        self.message_id = message_id
        self.timestamp = timestamp
        self.sender = sender
        self.parent = parent_id
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
