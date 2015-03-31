class Server(object):
    def __init__(self, id, era):
        self.id = id
        self.era = era
    def __eq__(self, other):
        if hasattr(other, 'era') and hasattr(other, 'id'):
            return self.id == other.id and self.era == other.era

class User(object):
    def __init__(self, name, server_era, user_id, server_id):
        self.name = name
        self.id = user_id.split('-')[0]
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
        attrs = ['name', 'id', 'session', 'server']
        for attr in attrs:
            if not hasattr(other, attr):
                return False
        return self.name == other.name\
                and self.id == other.id \
                and self.session == other.session \
                and self.server == other.server


