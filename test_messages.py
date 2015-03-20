import unittest

class TestMessages(unittest.TestCase):
	sample_data = [
		'{"id":"","type":"ping-event","data":{"time":1426697160,"next":1426697190}}',
		'{"id":"","type":"send-event","data":{"id":"00arxp1ofjhts","parent":"","time":1426698997,"sender":{"id":"e01253b4389655cf-0000011d","name":"mantis2","server_id":"heim.4","server_era":"00apdikn95eyo"},"content":"/me waves bye for a bit"}}',
		'{"id":"17","type":"send-reply","data":{"id":"00astcu2uj0n4","parent":"00ast9qvv8w74","time":1426720292,"sender":{"id":"889f5ecba53ecdc7-0000004f","name":"Drex (ð¨)","server_id":"heim.1","server_era":"00as6ru6tjgn4"},"content":"gotcha :D"}}',
		'{"id":"","type":"nick-event","data":{"id":"d81cb5df141851da-00000009","from":"","to":"Rubbery Negative Space"}}',
	]

	def setUp(self):
		pass

	def tearDown(self):
		pass