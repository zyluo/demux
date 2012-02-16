# encoding: utf-8
#
# Task worker - design 2
# Adds pub-sub flow to receive and respond to kill signal
#
# Author: Jeremy Avnet (brainsik) <spork(dash)zmq(at)theory(dot)org>
#

import json
import sys
import time
import zmq

if len(sys.argv) <> 2:
    print "usage: python %s [1-3]" % sys.argv[0]
    sys.exit(0)

worker_id = sys.argv[1]
if worker_id not in ['1', '2', '3']:
    print "usage: python %s [1-3]" % sys.argv[0]
    sys.exit(0)

context = zmq.Context()

# Socket for control input
broadcast = context.socket(zmq.SUB)
broadcast.connect("tcp://localhost:5558")
broadcast.setsockopt(zmq.SUBSCRIBE, "lb")

# Socket to send messages to
feedback = context.socket(zmq.PUSH)
feedback.connect("tcp://localhost:5559")

# Process messages from broadcast
poller = zmq.Poller()
poller.register(broadcast, zmq.POLLIN)

# Process messages from both sockets
while True:
    socks = dict(poller.poll())
    if socks.get(broadcast) == zmq.POLLIN:
        msg_type, msg_id, msg_body = broadcast.recv_multipart()
        # Process task
        message = json.loads(msg_body)
        if message['dest'] in ['ALL', worker_id]:
            print message['cmd'], message['opt']
        # Send results to feedback
        feedback.send_multipart([msg_type, msg_id,
                                 json.dumps({'worker_id': worker_id,
                                             'status': 200})])
