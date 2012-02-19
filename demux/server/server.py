# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import json
import sys
import zmq

import db

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
msg_type = None
msg_id = None
msg_json = None
msg_body = None
code = 0
desc = "OK"
while True:
    socks = dict(poller.poll())
    if socks.get(handler) == zmq.POLLIN:
        msg_type, msg_id, msg_json = handler.recv_multipart()
        msg_body = json.loads(msg_json)
    if socks.get(handler) == zmq.POLLOUT:
        cmd = "asdf"
        try:
            cmd = msg_body['cmd']
            msg = msg_body['msg']
            if cmd not in ['create_lb', 'delete_lb', 'read_lb', 'read_lb_list',
                           'update_lb_config', 'update_lb_instances',
                           'update_lb_http_server_names']:
                raise Exception("Invalid command")
            # access db and get return msg
            db_msg_body = getattr(db, cmd)(**msg)
            print db_msg_body
            code = 200
            desc = 'OK'
        except Exception, e:
            print e
            code = 500
            desc = str(e)
        # make msg to client and worker
        cli_msg_body = {'code': code, 'desc': desc}
        if code == 200:
            if cmd in ['read_lb', 'read_lb_list']:
                db_msg_body.update(cli_msg_body)
                cli_msg_body = db_msg_body
            else:
                #broadcast.send_multipart([msg_type, msg_id, msg_body])
                pass
        handler.send_multipart([msg_type, msg_id,
                                json.dumps({'cmd': cmd,
                                            'msg': cli_msg_body})])
        print 'b>', msg_id
    if socks.get(feedback) == zmq.POLLIN:
        report = feedback.recv_multipart()
        # handle feedback
        print 'f<', report
