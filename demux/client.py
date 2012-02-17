#!/usr/bin/env python

import json
import random
import time
import uuid
import zmq

class Client(object):

    def __init__(self, protocol="tcp", host="localhost", port="80"):
        url = "%s://%s:%s" % (protocol, host, port)
        context = zmq.Context()
        self.handler = context.socket(zmq.REQ)
        self.handler.connect(url)

    def __del__(self):
        self.handler.close()

    def send(self, msg_type, msg_id, msg_body):
        self.handler.send_multipart([msg_type, msg_id, json.dumps(msg_body)])
        return self.handler.recv_multipart()

if __name__ == '__main__':
    # Initialize random number generator
    random.seed()
    msg_body = {'cmd': 'read_lb_list',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': "lzyeval",
                        'tenant': "weipan",
                       }
               }

    # Make message
    msg_type = 'lb'
    msg_id = str(uuid.uuid1())

    client = Client(protocol='tcp', host='localhost', port='5557')
    ack = client.send(msg_type, msg_id, msg_body)

    print
    print '>', msg_body
    print '<', ack
    print

    msg_body = {'cmd': 'read_lb',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': "lzyeval",
                        'tenant': "weipan",
                        'load_balancer_id': "myHTTPlb",
                       }
               }
    ack = client.send(msg_type, msg_id, msg_body)
    print
    print '>', msg_body
    print '<', ack
    print
