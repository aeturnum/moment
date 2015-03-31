import unittest
from models import User
from packets import get_message_object, EuphoriaPing, EuphoriaMessage
import json

class TestMessages(unittest.TestCase):
    sample_ping = '{"id":"","type":"ping-event","data":{"time":1426697160,"next":1426697190}}'
    sample_send = '{"id":"","type":"send-event","data":{"id":"00arxp1ofjhts","parent":"","time":1426698997,"sender":{"id":"d47f41e91c10b34a-00000008","name":"Drex","server_id":"heim.1","server_era":"00awjcddxlkhs"},"content":"/me waves bye for a bit"}}'
    sample_reply = '{"id":"17","type":"send-reply","data":{"id":"00astcu2uj0n4","parent":"00ast9qvv8w74","time":1426720292,"sender":{"id":"889f5ecba53ecdc7-0000004f","name":"Drex (ð¨)","server_id":"heim.1","server_era":"00as6ru6tjgn4"},"content":"gotcha :D"}}'
    sample_nick = '{"id":"","type":"nick-event","data":{"id":"d81cb5df141851da-00000009","from":"","to":"Rubbery Negative Space"}}'
    sample_user = '{"id":"d47f41e91c10b34a-00000008","name":"Drex","server_id":"heim.1","server_era":"00awjcddxlkhs"}'
    sample_snapshot = """
    {"id":"","type":"snapshot-event",
    "data":{"session_id":"889f5ecba53ecdc7-00000008","version":"054eb92661f5de57aa94d3de538fd5988f1caabe",
    "listing":[{"id":"d47f41e91c10b34a-00000008","name":"Drex","server_id":"heim.1","server_era":"00awjcddxlkhs"},
    {"id":"fe083605e43d3dbc-00000001","name":"chromakode","server_id":"heim.4","server_era":"00awje13l8y68"},
    {"id":"4bd44ba37679d74d-0000000c","name":"intortus","server_id":"heim.3","server_era":"00awjd42wo0e8"}],
    "log":[{"id":"00avxhybe3da8","parent":"00avwx7xstreo","time":1426795719,"sender":{"id":"889f5ecba53ecdc7-000000c9","name":"Drex (ð¨)","server_id":"heim.1","server_era":"00asububwunsw"},"content":"maybe there's an API that plugins can access - send message to server, create message, delete message, etc"},
    {"id":"00avxi5qb8rgg","parent":"00avxhybe3da8","time":1426795723,"sender":{"id":"889f5ecba53ecdc7-000000c9","name":"Drex (ð¨)","server_id":"heim.1","server_era":"00asububwunsw"},"content":"that's common"},
    {"id":"00avxi8cas7pc","parent":"00avwx7xstreo","time":1426795724,"sender":{"id":"4bd44ba37679d74d-0000008e","name":"intortus","server_id":"heim.3","server_era":"00asuckln9on4"},"content":"where \"norman in the sidebar\" can be expressed according to some standard"},
    {"id":"00avxie5u2z28","parent":"00avwx7xstreo","time":1426795728,"sender":{"id":"fe083605e43d3dbc-000000ca","name":"chromakode","server_id":"heim.4","server_era":"00asudd8w5yww"},"content":"however, anything more specific than that will need to be custom"},
    {"id":"00avxj9b00a9s","parent":"00avwx7xstreo","time":1426795743,"sender":{"id":"fe083605e43d3dbc-000000ca","name":"chromakode","server_id":"heim.4","server_era":"00asudd8w5yww"},"content":"oh totally, norman in the sidebar probably won't be a plugin per se-- a lot of the room customization stuff will be in the core featureset"}'"""

    def setUp(self):
        pass

    def test_ping_construction(self):
        expected_sent = 1426697160
        expected_next = 1426697190
        ping  = EuphoriaPing(json.loads(self.sample_ping))
        ping2 = get_message_object(self.sample_ping)
        self.assertEqual(ping, ping)
        self.assertEqual(ping, ping2)
        self.assertEqual(ping.sent_time, expected_sent)
        self.assertEqual(ping.next_time, expected_next)
        self.assertEqual(ping2.sent_time, expected_sent)
        self.assertEqual(ping2.next_time, expected_next)

    def test_user_construction(self):
        expected_username = 'Drex'
        expected_id = 'd47f41e91c10b34a'
        expected_session = '00000008'
        expected_server_id = 'heim.1'
        expected_server_era = '00awjcddxlkhs'
        user = User.create(json.loads(self.sample_user))
        user2 = get_message_object(self.sample_user)
        self.assertEqual(user, user)
        self.assertEqual(user, user2)
        users = [user, user2]
        for u in users:
            self.assertEqual(u.name, expected_username)
            self.assertEqual(u.server.id, expected_server_id)
            self.assertEqual(u.server.era, expected_server_era)
            self.assertEqual(u.session, expected_session)
            self.assertEqual(u.id, expected_id)

    def test_message_construction(self):
        #  '{"id":"","type":"send-event",
        #     "data":{
        #        "id":"00arxp1ofjhts",
        #         "parent":"",
        #         "time":1426698997,
        #         "sender":{"id":"d47f41e91c10b34a-00000008","name":"Drex","server_id":"heim.1","server_era":"00awjcddxlkhs"}
        #         ,"content":"/me waves bye for a bit"}}'
        expected_user = get_message_object(self.sample_user)
        expected_id = '00arxp1ofjhts'
        expected_parent = ''
        expected_time = 1426698997
        expected_content = '/me waves bye for a bit'
        message = EuphoriaMessage(json.loads(self.sample_send))
        message2 = get_message_object(self.sample_send)
        print(message)
        print(message2)
        self.assertEqual(message, message2)
        messages = [message, message2]
        for m in messages:
            self.assertEqual(message.message_id, expected_id)
            self.assertEqual(message.timestamp, expected_time)
            self.assertEqual(message.parent, expected_parent)
            self.assertEqual(message.content, expected_content)
            self.assertEqual(message.sender, expected_user)
    def tearDown(self):
        pass
