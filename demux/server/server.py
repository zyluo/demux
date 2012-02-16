# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import json
import sys
import zmq

context = zmq.Context()

# Socket to receive messages on
handler = context.socket(zmq.REP)
handler.bind("tcp://*:5557")

# Socket to send messages on
broadcast = context.socket(zmq.PUB)
broadcast.bind("tcp://*:5558")

# Socket with direct access to the feedback: used to syncronize start of batch
feedback = context.socket(zmq.PULL)
feedback.bind("tcp://*:5559")

poller = zmq.Poller()
poller.register(handler, zmq.POLLIN|zmq.POLLOUT)
poller.register(feedback, zmq.POLLIN)

message = None
while True:
    socks = dict(poller.poll())
    if socks.get(handler) == zmq.POLLIN:
        msg_type, msg_id, msg_body = handler.recv_multipart()
        # update database
        print
        print 'r=', msg_id
    if socks.get(handler) == zmq.POLLOUT:
        handler.send_multipart([msg_type, msg_id, json.dumps({'status': 200})])
        #broadcast.send_multipart([msg_type, msg_id, msg_body])
        # send response
        print 'b>', msg_id
    if socks.get(feedback) == zmq.POLLIN:
        report = feedback.recv_multipart()
        # handle feedback
        print 'f<', report
