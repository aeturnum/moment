import time

class EuphoriaUser(object):
	def __init__(self, name, server_era, user_id, server_id):
		self.name = name
		self.id = user_id.split('-')[0]
		self.session = user_id.split('-')[0]
		self.server = {
			'id':server_id,
			'era':server_era
		}

	def __str__(self):
		return '[{}]'.format(self.name)

	@staticmethod
	def create(message):
		u = EuphoriaUser(message['name'], message['server_era'], message['id'], message['server_id'])
		return u

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
			return '{}{}| {}<{}{}>'.format(index_str, time.strftime("%H:%M:%S", local_time), '| '*depth, self.sender.name, self.content.replace('/me', ''))
		else:
			return '{}{}| {}{}: {}'.format(index_str, time.strftime("%H:%M:%S", local_time), '| '*depth, self.sender, self.content)

	def __str__(self):
		local_time = time.localtime(self.timestamp)
		return '{}|{}: {}'.format(time.strftime("%H:%M:%S", local_time), self.sender, self.content)

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

class EuphoriaPing(object):
	def __init__(self, sent_time, next_ping):
		self.sent_time = sent_time
		self.next_time = next_ping

	def __str__(self):
		return 'ping[{}]->{}'.format(self.sent_time, self.next_time)

	@staticmethod
	def create(message):
		if 'data' in message:
			message = message['data']
		p = EuphoriaPing(message['time'], message['next'])

		return p

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
			for user in self.listing:
				add_user(user)
		return self._users

	@property
	def messages(self):
		if not self._users:
			for user in self.listing:
				add_user(user)
		return self._users

	@staticmethod
	def create(message):
		ss = EuphoriaSnapshot(
			message['data']['version'],
			message['data']['session_id'],
			message['data']['log'], 
			message['data']['listing']),

def get_message_object(message):
	type_to_class_map = {
		'ping-event': EuphoriaPing,
		'snapshot-event': EuphoriaSnapshot,
		'send-event': EuphoriaMessage,
		'send-reply': EuphoriaMessage, # do something about this?
		'part-event': None
	}

	if message['type'] in type_to_class_map:
		type_class = type_to_class_map[message['type']]
		if type_class:
			return type_class.create(message)

	return None

