#!/usr/bin/env python

import MySQLdb
import MySQLdb.cursors

db = MySQLdb.connect(host="localhost", passwd="asdf",
                   user="nova", db="nova",
                   cursorclass=MySQLdb.cursors.DictCursor) 
cu = db.cursor()

insert_lb = ("INSERT INTO load_balancer "
                         "(id, protocol, listen_port, "
                          "instance_port, balanceing_method, "
                          "health_checkout_timeout_ms, "
                          "health_check_interval_ms, "
                          "health_checkout_target_path, "
                          "health_check_fail_count, "
                          "health_checkout_health_threshold, "
                          "health_check_unhealthy_threshold) "
             "VALUES (%(load_balancer_id)s, %(protocol)s, %(listen_port)s, "
                     "%(instance_port)s, %(balancing_method)s, "
                     "%(health_check_timeout_ms)s, "
                     "%(health_check_interval_ms)s, "
                     "%(health_check_target_path)s, "
                     "%(health_check_fail_count)s, "
                     "%(health_check_healthy_threshold)s, "
                     "%(health_check_unhealthy_threshold)s);")

insert_instance_id = ("INSERT INTO load_balancer_instance_association "
                                  "(load_balancer_id, instance_id) "
                      "VALUES (%(load_balancer_id)s, %(instance_id)s);")

insert_http_server_name = ("INSERT INTO load_balancer_instance_association "
                                       "(id, load_balancer_id) "
                           "VALUES (%(http_server_name)s, "
                                   "%(load_balancer_id)s);")

delete_lb = ("UPDATE load_balancer SET deleted=True "
             "WHERE id=%(load_balancer_id)s;")

select_lb = ("SELECT id as load_balancer_id, balancing_method, "
                    "health_check_timeout_ms, health_check_interval_ms, "
                    "health_check_target_path, health_check_fail_count, "
                    "health_check_healthy_threshold, "
                    "health_check_unhealthy_threshold, user_id as user_name, "
                    "project_id as tenant "
             "FROM load_balancer lb "
             "WHERE deleted is FALSE "
                     "AND user_id=%(user_name)s "
                     "AND project_id=%(tenant)s "
                     "AND id=%(load_balancer_id)s;")

select_lb_list = ("SELECT id as load_balancer_id, protocol, listen_port, "
                               "instance_port "
                  "FROM load_balancer "
                  "WHERE deleted is FALSE "
                        "AND user_id=%(user_name)s "
                        "AND project_id=%(tenant)s;")

select_instance_project = ("SELECT count(*) FROM user_project_association "
                           "WHERE deleted is FALSE "
                                   "AND user_id=%(user_id)s "
                                   "AND project_id=%(tenant)s;")

select_http_servers = ("SELECT count(*) FROM user_project_association "
                           "WHERE deleted is FALSE "
                                   "AND user_id=%(user_id)s "
                                   "AND project_id=%(tenant)s;")

select_fixed_ips = ("SELECT j.address FROM instances i, fixed_ips j "
                    "WHERE i.deleted is FALSE "
                            "AND i.id=j.id "
                            "AND i.uuid=%s(instance_uuid)s ")

def create_lb(*args, **kwargs):
    pass

def read_lb(*args, **kwargs):
    cnt = cu.execute(select_lb, kwargs)
    lb = cu.fetchone()
    return lb

def read_lb_list(*args, **kwargs):
    cnt = cu.execute(select_lb_list, kwargs)
    lb_list = cu.fetchall()
    return {"load_balancer_list": lb_list,
            "user_name": kwargs.get("user_name"),
            "tenant": kwargs.get("tenant")}

def update_lb_config(*args, **kwargs):
    pass

def update_lb_instance_ids(*args, **kwargs):
    pass

def update_lb_http_server_names(*args, **kwargs):
    pass

def delete_lb(*args, **kwargs):
    pass
