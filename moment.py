# libs needed: urwid, websocket-client
# 'q' to quit
# read only
# will probably crash when someone joins the room 

import json
import time
import urwid
import sys
import threading
from websocket import create_connection

users = {}
messages = {}
message_trees = []

class EuphoriaUser(object):
	def __init__(self, name, server_era, user_id, server_id):
		self.name = name
		self.id = user_id.split('-')[0]
		self.id_suffix = user_id.split('-')[0]
		self.server = {
			'id':server_id,
			'era':server_era
		}

	def __str__(self):
		return '[{}]'.format(self.name)

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

class EuphoriaMessageTree(object):
	def __init__(self, message, depth=0):
		self.message = message
		self.children = []
		self.depth = depth

	def add(self, message):
		if message.parent == "":
			raise Exception("Added message to tree that was not at top! {}".format(message))
		else:
			if message.parent == self.message.id:
				new_tree = EuphoriaMessageTree(message, self.depth + 1)
				self.children.append(new_tree)
				self.children = sorted(self.children)
				return True
			else:
				for c in self.children:
					if c.add(message):
						return True

		return False


	def __lt__(self, other):
		return self.message < other.message

	def to_urwid(self, start_index=None):
		t = urwid.Text(self.message.urwid_string(self.depth, start_index), align='left')
		urwid_elements = [t]
		if start_index:
			start_index += 1
		for c in self.children:
			urwid_elements.extend(c.to_urwid(start_index))
			if start_index:
				start_index += c.size()

		return urwid_elements

	def __str__(self):
		s = '{}{}'.format('\t'*self.depth, self.message)
		for c in self.children:
			s += '\n{}'.format(c)
		return s

class EuphoriaRoom(object):
	def __init__(self, message_trees):
		self.trees = message_trees
		self.unprocessed_messages = []

	def set_display_list(self, display_list):
		self.display_list = display_list
		self.update_display()

	def update_display(self):
		del self.display_list[:]
		self.display_list.extend(self.element_list())

	def element_list(self):
		elements = []
		for t in self.trees:
			elements.extend(t.to_urwid())

		return elements

	def add_message(self, m):
		added = False
		if m.parent == '':
			m = EuphoriaMessageTree(m)
			self.trees.append(m)
			self.trees = sorted(self.trees)
			added = True
		else:
			main_offset = 0
			for t in self.trees:
				if t.add(m):
					added = True
					break

		to_remove = []
		
		for t in self.trees:
			for um in self.unprocessed_messages:
				if t.add(um):
					to_remove.append(um)
			if not added and t.add(m):
				added = True

		for um in to_remove:
			self.unprocessed_messages.remove(um)

		if not added:
			# maybe we don't have the parents yet
			self.unprocessed_messages.append(m)

	def __str__(self):
		s = ''
		for t in self.trees:
			s += '{}\n'.format( t)
		return s
			

class EuphoriaPing(object):
	def __init__(self, sent_time, next_ping):
		self.sent_time = sent_time
		self.next_time = next_ping

	def __str__(self):
		return 'ping[{}]->{}'.format(self.sent_time, self.next_time)

def add_user(user_data):
	u = EuphoriaUser(user_data['name'], user_data['server_era'], user_data['id'], user_data['server_id'])
	if u.id not in users:
		users[u.id] = u
	return u

def add_message(message_data):
	u = add_user(message_data['sender'])
	m = EuphoriaMessage(
				message_data['id'],
				message_data['time'],
				u,
				message_data['parent'],
				message_data['content'])	
	messages[m.id] = m
	return m

def handle_send_event(event_data, room):
	m = add_message(event_data)
	room.add_message(m)
	room.update_display()

def handle_euphoria_snapshot(messages, users, room):
	for user in users:
		add_user(user)

	for message in messages:
		m = add_message(message)
		room.add_message(m)

class EuphoriaSnapshot(object):
	def __init__(self, version, log, session_id, listing):
		self.version = version
		self.session_id = session_id
		self.log = log
		self.listing = listing
		self._process_data()

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    txt.set_text(repr(key))

class EuphoriaFactory(object):
	constructors = {
		'ping-event': lambda x, y: EuphoriaPing(x['data']['time'], x['data']['next']),
		#'snapshot-event': lambda x, y: EuphoriaSnapshot(x['data']['version'], x['data']['log'], x['data']['session_id'], x['data']['listing']),
		'snapshot-event': lambda x, y: handle_euphoria_snapshot(x['data']['log'], x['data']['listing'], y),
		'send-event': lambda x, y: handle_send_event(x['data'], y),
		'part-event':lambda x, y: print('part-event')
	}

	@staticmethod
	def get_object(websocket_message, room):
		try:
			constructor = EuphoriaFactory.constructors[websocket_message['type']]
		except KeyError:
			print(json.dumps(websocket_message))
			raise KeyError("Did not have constructor for {}! \n{}".format(websocket_message['type']))
		
		return constructor(websocket_message, room)

def process_euphoria_message(message, list_walker = []):
	json_data = json.loads(message)
	if 'id' in json_data:
		EuphoriaFactory.get_object(json_data, list_walker)

room = 'space'
if __name__ == "__main__":
	if len(sys.argv) > 1:
		if len(sys.argv) > 2:
			print("Usage: python3 ./cli_client.py <room name> (default room: space)")
			sys.exit(1)
		room = sys.argv[1]

ws = create_connection("wss://euphoria.io/room/{}/ws".format(room))

room = EuphoriaRoom([])

list_walker =	urwid.SimpleFocusListWalker([])
room.set_display_list(list_walker)

event_loop = urwid.SelectEventLoop()

ws_data = []
lock = threading.Lock()
shutdown_event = threading.Event()

exit_button = urwid.Button('Exit')

def exit_program(button):
	shutdown_event.set()
	exit_button.set_label("Exiting program.....")
	ws.close()
	raise urwid.ExitMainLoop()

def exit_on_q(key):
	if key in ('q', 'Q'):
		exit_program(None)


def check_ws(ws, lock, event):
	while True:
		new_data = None
		try:
			new_data = ws.recv()
		except:
			if shutdown_event.is_set():
				pass
			else:
				raise
		lock.acquire()
		if new_data:
			ws_data.append(new_data)
		lock.release()
		if shutdown_event.is_set():
			break

t = threading.Thread(target=check_ws, args=(ws,lock,shutdown_event,))


def update():
	message = None
	if lock.acquire(False):
		if len(ws_data):
			message = ws_data.pop(0)
		lock.release()
	if message:
		process_euphoria_message(message, room)
		del list_walker[:]
		list_walker.extend(room.element_list())

	if not shutdown_event.is_set():
		event_loop.alarm(0.1, update)


event_loop.alarm(0.1, update)

urwid.connect_signal(exit_button, 'click', exit_program)

header = urwid.AttrWrap(urwid.Text("Euphoria"), 'header')
listbox = urwid.ListBox(list_walker)
footer = urwid.AttrWrap(exit_button, 'footer')
frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header, footer=footer)

palette = [
    ('banner', 'black', 'light gray'),
    ('streak', 'black', 'dark red'),
    ('bg', 'black', 'dark blue'),]
screen = urwid.raw_display.Screen()

t.start()
urwid.MainLoop(frame, palette, screen, event_loop=event_loop, unhandled_input=exit_on_q).run()

ws.close()
t.join(1)