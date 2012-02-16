
msg_type = 'lb'
msg_id = str(uuid.uuid1())

======== client -> server ==============

# create_lb
msg_body = {'cmd': 'create_lb',   
            'msg': {'user_id': 'myUser',
                    'project_id': 'myProject',
                    'load_balancer_id': 'myLB',
                    'protocol': random.choice(['http', 'tcp']),
                    'listen_port': 80,
                    'instance_port': 80,
                    'balancing_method': random.choice(['a_meth', 'round_robin']),
                    'health_check': {'timeout_ms': 5,
                                     'interval_ms': 0.5
                                     # if http
                                     'target_path': '/'
                                     'fail_count': 2
                                     # elif tcp
                                     'healthy_treshold':10,
                                     'unhealthy_treshold':2,
                                    },
                    'instance_ids': [23, 44, 82]
                    'http_server_names': ['www.abc.com', 'www.xyz.com']
                   }
           }

# delete or 'read_lb'
message = {'cmd': random.choice(['delete_lb','read_lb'])
           'msg': {'user_id': 'myUser'
                   'project_id': 'myLB'
                   'load_balancer_id': 'myLB',
                   }
           }

# 'read_all_lb'
message = {'cmd': 'read_all_lb',
           'msg': {'user_id': 'myUser'
                   'project_id': 'myLB'
                   }
           }
# update

# After you create a load balancer, you can modify any of the settings,
# except for Load Balancer Name and Port Configuration.

# To rename a load balancer or change its port configuration,
# create a replacement load balancer.

# update 一个或多个字段
message = {'cmd': 'update_lb_metadata',   
           'msg': {'user_id': 'myUser',
                   'project_id': 'myProject',
                   'load_balancer_id': 'myLB',
                   'balancing_method': random.choice(['a_meth', 'round_robin']),
                   'health_check': {'timeout_ms': 5,
                                    'interval_ms': 0.5
                                    # if http
                                    'target_path': '/'
                                    'fail_count': 2
                                    # elif tcp
                                    'healthy_treshold':10,
                                    'unhealthy_treshold':2,
                                    },
                   }
           }

# update instances
message = {'cmd': 'update_lb_instance_ids',   
           'msg': {'user_id': 12,
                   'project_id': 'myProject',
                   'load_balancer_id': 'myLB',
                   'instance_ids': [id1, id2]
                   }
           }

# update http_server_names
message = {'cmd': 'update_lb_instance_ids',   
           'msg': {'user_id': 12,
                   'project_id': 'myProject',
                   'load_balancer_id': 'myLB',
                   'http_server_names': ['www.abc.com', 'www.xyz.com']
                   }
           }

======== server -> client ==============

======== server -> worker ==============

to_worker = {'cmd': random.choice('create_lb', 'update_lb'),
             'msg': {'user_id': 'myUser',
                     'project_id': 'myProject',
                     'load_balancer_id': 'myLB',
                     'protocol': random.choice(['http', 'tcp']),
                     'listen_port': 80,
                     'instance_port': 80,
                     'balancing_method': random.choice(['a_meth', 'round_robin']),
                     'health_check': {'timeout_ms': 5,
                                      'interval_ms': 0.5
                                      # if http
                                      'target_path': '/'
                                      'fail_count': 2
                                      # elif tcp
                                      'healthy_treshold':10,
                                      'unhealthy_treshold':2,
                                     },
                     'instance_ids': [23, 44, 82]
                     # add instance fixed ips and send to worker
                     'instance_ips': ['10.4.5.6', '10.3.4.5', '10.8.8.8']
                     'http_server_names': ['www.abc.com', 'www.xyz.com']
                    }
            }

to_worker= {'cmd': 'delete_lb',
            'msg': {'user_id': 'myUser'
                    'project_id': 'myLB'
                    'load_balancer_id': 'myLB',
                   }
           }

======== worker -> server ==============

from_worker = {'cmd': <cmd>,
               'msg' {'code': 200,
                      'desc': 'sdkf;askjdgfa'
                     }
              }
