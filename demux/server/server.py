# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import ConfigParser
import json
import sys
import traceback

import zmq

import db

config = ConfigParser.ConfigParser()
config.read("demux.conf")
server_cfg = dict(config.items('Demux'))

context = zmq.Context()

# Socket to receive messages on
handler = context.socket(zmq.REP)
handler.bind("tcp://%(handler_host)s:%(handler_port)s" % server_cfg)

# Socket to send messages on
broadcast = context.socket(zmq.PUB)
broadcast.bind("tcp://%(broadcast_host)s:%(broadcast_port)s" % server_cfg)

# Socket with direct access to the feedback: used to syncronize start of batch
feedback = context.socket(zmq.PULL)
feedback.bind("tcp://%(feedback_host)s:%(feedback_port)s" % server_cfg)

poller = zmq.Poller()
poller.register(handler, zmq.POLLIN | zmq.POLLOUT)
poller.register(feedback, zmq.POLLIN)


def get_work_msg(cmd, **msg):
    res = db.read_whole_lb(**msg)
    if cmd == "delete_lb":
        res = dict(filter(lambda (x, y): x in ['user_name', 'tenant',
                                               'load_balancer_id',
                                               'protocol'], res.items()))
    return res


while True:
    socks = dict(poller.poll())
    if socks.get(handler) == zmq.POLLIN:
        msg_type, msg_id, msg_json = handler.recv_multipart()
        msg_body = json.loads(msg_json)
        cli_msg = {'code': 200, 'desc': 'OK'}
        try:
            cmd = msg_body['cmd']
            msg = msg_body['msg']
            print cmd, msg
            print
            # access db and get return msg
            if cmd in ['read_lb', 'read_lb_list', 'read_load_balancer_id_all',
                       'read_http_server_name_all']:
                db_res = getattr(db, cmd)(**msg)
                cli_msg.update(db_res)
            elif cmd in ['create_lb', 'delete_lb', 'update_lb_config',
                         'update_lb_instances', 'update_lb_http_server_names']:
                getattr(db, cmd)(**msg)
                work_cmd = "update_lb" if cmd.startswith("update_lb") else cmd
                work_msg = get_work_msg(cmd, **msg)
                print ">>>>>>>>>", work_msg
                print
                broadcast.send_multipart([msg_type, msg_id,
                                          json.dumps({'cmd': work_cmd,
                                                      'msg': work_msg})])
            else:
                raise Exception("Invalid command")
        except Exception, e:
            print traceback.format_exc()
            cli_msg['code'] = 500
            cli_msg['desc'] = str(e)
        print cmd, cli_msg
        print
        handler.send_multipart([msg_type, msg_id,
                                json.dumps({'cmd': cmd,
                                            'msg': cli_msg})])
    if socks.get(feedback) == zmq.POLLIN:
        report = feedback.recv_multipart()
        # handle feedback
        print 'w>', report
