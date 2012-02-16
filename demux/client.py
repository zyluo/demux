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
        self.handler.send_multipart([msg_type, msg_id, json.dumps(message)])
        return self.handler.recv_multipart()

if __name__ == '__main__':
    # Initialize random number generator
    random.seed()
    message = {'cmd': 'createlb',
               'dest': random.choice(['ALL', '1', '2', '3']),
               'opt': {'user_id': 12,
                       'site_id': 8,
                       'protocol': random.choice(['http', 'tcp']),
                       'instances': [{'id': 4,
                                      'port': random.choice([8080, 7788, 5559]),
                                      'timeout': 5},
                                     {'id': 91,
                                      'port': random.choice([8080, 7788, 5559]),
                                      'timeout': 10},
                                    ],
                      }
              }

    # Make message
    msg_type = 'lb'
    msg_id = str(uuid.uuid1())
    msg_body = json.dumps(message)

    client = Client(protocol='tcp', host='localhost', port='5557')
    ack = client.send(msg_type, msg_id, msg_body)

    print
    print '>', message
    print '<', ack
    print
