# libs needed: urwid, websocket-client
# 'q' to quit
# read only
# will probably crash when someone joins the room 

import json
import time
import urwid
import sys
import threading
from queue import Queue

from websocket import create_connection

from models import User, Message
from packets import EuphoriaPing, parse_euphoria_packet

users = {}
messages = {}
message_trees = []

class EuphoriaMessageTree(object):
	def __init__(self, message, depth=0):
		self.message = message
		self.children = []
		self.depth = depth

	def add(self, message):
		if message.parent == "":
			raise Exception("Added message to tree that was not at top! {}".format(message))
		else:
			if message.parent == self.message.message_id:
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
	def __init__(self, name):
		self.name = name
		self.ws = None
		self.lock = threading.Lock()
		self.server_packets = Queue()
		self.packets_to_send = Queue()
		self.websocket_thread = None
		self.trees = []
		self.unprocessed_messages = []
		self.users = {}
		self.display_list = urwid.SimpleFocusListWalker([])
		self.message_id_number = 0

	def __del__(self):
		if self.ws:
			self.ws.close()
		if self.websocket_thread:
			self.websocket_thread.join(1)

	@staticmethod
	def check_ws(ws, event, packets_from_server, packets_to_send):
		while True:
			new_data = None
			if not packets_to_send.empty():
				send_packet = packets_to_send.get(False)
				if send_packet:
					ws.send(send_packet)
			try:
				new_data = ws.recv()
			except:
				if event.is_set():
					return
				else:
					raise
			if new_data:
				packets_from_server.put(new_data, True)
			if event.is_set():
				return

	def connect(self, shutdown_event):
		self.ws = create_connection("wss://euphoria.io/room/{}/ws".format(self.name))
		self.websocket_thread = threading.Thread(
			target=EuphoriaRoom.check_ws, 
			args=(self.ws,shutdown_event,self.server_packets,self.packets_to_send,))
		self.websocket_thread.start()


	def process_euphoria_packet(self, packet):
		packet_object = parse_euphoria_packet(packet)
		# packet might not be supported yet
		if packet_object:
			updated = False
			for u in packet_object.users:
				room.add_user(u)
				#soon
				#updated = True
			for m in packet_object.messages:
				room.add_message(m)
				updated = True

			if updated:
				room.update_display()

			if packet_object.packet_type == 'ping-event':
				ping_reply = {"type":"ping-reply","data":{"time":int(time.time())},"id":str(self.message_id_number)}
				self.message_id_number += 1
				self.packets_to_send.put(json.dumps(ping_reply), True) 

	# there must be a better way
	def generate_update_function(self, update_loop):
		def update():
			message = None
			if not self.server_packets.empty():
				message = self.server_packets.get()
			if message:
				self.process_euphoria_packet(message)

			if not shutdown_event.is_set():
				event_loop.alarm(0.1, update)

		return update

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

	def add_user(self, user):
		self.users[user.user_id] = user

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
			

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    txt.set_text(repr(key))

room_name = 'space'
if __name__ == "__main__":
	if len(sys.argv) > 1:
		if len(sys.argv) > 2:
			print("Usage: python3 ./cli_client.py <room name> (default room: space)")
			sys.exit(1)
		room_name = sys.argv[1]

room = EuphoriaRoom(room_name)

event_loop = urwid.SelectEventLoop()

shutdown_event = threading.Event()

exit_button = urwid.Button('Exit')

def exit_program(button):
	shutdown_event.set()
	exit_button.set_label("Exiting program.....")
	raise urwid.ExitMainLoop()

def exit_on_q(key):
	if key in ('q', 'Q'):
		exit_program(None)

room.connect(shutdown_event)
update = room.generate_update_function(event_loop)

event_loop.alarm(0.1, update)

urwid.connect_signal(exit_button, 'click', exit_program)

header = urwid.AttrWrap(urwid.Text("Euphoria - {}".format(room.name)), 'header')
listbox = urwid.ListBox(room.display_list)
footer = urwid.AttrWrap(exit_button, 'footer')
frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header, footer=footer)

palette = [
    ('banner', 'black', 'light gray'),
    ('streak', 'black', 'dark red'),
    ('bg', 'black', 'dark blue'),]
screen = urwid.raw_display.Screen()

urwid.MainLoop(frame, palette, screen, event_loop=event_loop, unhandled_input=exit_on_q).run()
