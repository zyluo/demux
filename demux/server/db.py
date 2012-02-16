#!/usr/bin/env python

import MySQLdb

insert_lb = ("INSERT INTO load_balancer (id, protocol, listen_port, "
                                        "balanceing_method, "
                                        "health_checkout_timeout_ms, "
                                        "health_check_interval_ms, "
                                        "health_checkout_target_path, "
                                        "health_check_fail_count, "
                                        "health_checkout_health_threshold, "
                                        "health_check_unhealthy_threshold) "
             "VALUES (%(load_balancer_id) ")

def create_lb(user_id, project_id, lb_id, **kwargs):
    pass

def read_lb(user_id, project_id, lb_id):
    pass

def read_all_lb(user_id, project_id):
    pass

def update_lb_metadata(lb_id, **kwargs):
    pass

def update_lb_instance_ids(lb_id, user_id, project_id, *instance_ids):
    pass

def update_lb_http_server_names(lb_id, user_id, project_id, *http_server_names):
    pass

def delete_lb(lb_id):
    pass

