#!/usr/bin/env python

import MySQLdb
import MySQLdb.cursors

db = MySQLdb.connect(host="localhost", passwd="passwd",
                     user="nova", db="nova",
                     cursorclass=MySQLdb.cursors.DictCursor) 
cu = db.cursor()

"""
insert_lb = ("INSERT INTO load_balancer (id) VALUES (%(load_balancer_id)s);")

cnt_instances = ("SELECT COUNT(*) FROM load_balancer_instance_association "
                 "WHERE deleted is FALSE "
                         "AND load_balancer_id=%(load_balancer_id)s")
"""

select_http_server_names = ("SELECT id FROM http_server_name "
                            "WHERE deleted is FALSE;")

select_listen_ports = ("SELECT listen_port FROM load_balancer "
                            "WHERE deleted is FALSE;")

select_lb = ("SELECT id as load_balancer_id, balancing_method, "
                    "health_check_timeout_ms, health_check_interval_ms, "
                    "health_check_target_path, health_check_fail_count, "
                    "health_check_healthy_threshold, "
                    "health_check_unhealthy_threshold, user_id as user_name, "
                    "project_id as tenant, protocol "
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

cnt_lb = ("SELECT COUNT(*) as lb_cnt FROM load_balancer "
          "WHERE deleted is FALSE "
                  "AND id=%(load_balancer_id)s")

hard_delete_lb_config = ("DELETE FROM load_balancer "
                         "WHERE id=%(load_balancer_id)s;")

delete_lb_config = ("UPDATE load_balancer SET deleted=True "
             "WHERE id=%(load_balancer_id)s;")

delete_instances = ("UPDATE load_balancer_instance_association "
                    "SET deleted=True "
                    "WHERE load_balancer_id=%(load_balancer_id)s ")

delete_http_server_names = ("UPDATE http_server_name SET deleted=True "
                            "WHERE load_balancer_id=%(load_balancer_id)s;")

"""
select_instance_project = ("SELECT count(*) FROM user_project_association "
                           "WHERE deleted is FALSE "
                                   "AND user_id=%(user_id)s "
                                   "AND project_id=%(tenant)s;")

select_http_servers = ("SELECT count(*) FROM user_project_association "
                           "WHERE deleted is FALSE "
                                   "AND user_id=%(user_id)s "
                                   "AND project_id=%(tenant)s;")
"""

select_fixed_ips = ("SELECT j.address FROM instances i, fixed_ips j "
                    "WHERE i.deleted is FALSE "
                            "AND i.id=j.id "
                            "AND i.uuid=%s;")

select_lb_instances = ("SELECT i.uuid FROM instances i,"
                               "load_balancer_instance_association a "
                       "WHERE i.deleted is FALSE "
                               "AND i.id=a.instance_id "
                               "AND a.load_balancer_id=%(load_balancer_id)s;")

select_lb_servernames = ("SELECT id FROM http_server_name "
                         "WHERE deleted is FALSE "
                                 "AND load_balancer_id=%(load_balancer_id)s")

select_instances_by_tenant = ("SELECT id AS instance_id, uuid "
                              "FROM instances "
                              "WHERE deleted=FALSE "
                                      "AND project_id=%(tenant)s;")

_update_lb_cfg = ("INSERT INTO load_balancer "
                              "(deleted, id, user_id, project_id, protocol, "
                              "listen_port, instance_port, balancing_method, "
                              "health_check_timeout_ms, "
                              "health_check_interval_ms, "
                              "health_check_target_path, "
                              "health_check_fail_count, "
                              "health_check_healthy_threshold, "
                              "health_check_unhealthy_threshold) "
                  "VALUES (FALSE, %(load_balancer_id)s, %(user_name)s, "
                                "%(tenant)s, %(protocol)s, "
                                "%(listen_port)s, %(instance_port)s, "
                                "%(balancing_method)s, "
                                "%(health_check_timeout_ms)s, "
                                "%(health_check_interval_ms)s, "
                                "%(health_check_target_path)s, "
                                "%(health_check_fail_count)s, "
                                "%(health_check_healthy_threshold)s, "
                                "%(health_check_unhealthy_threshold)s) "
                  "ON DUPLICATE KEY UPDATE "
                      "balancing_method=%(balancing_method)s, "
                      "health_check_timeout_ms=%(health_check_timeout_ms)s, "
                      "health_check_interval_ms=%(health_check_interval_ms)s, "
                      "health_check_target_path=%(health_check_target_path)s, "
                      "health_check_fail_count=%(health_check_fail_count)s, "
                      "health_check_healthy_threshold="
                              "%(health_check_healthy_threshold)s, "
                      "health_check_unhealthy_threshold="
                              "%(health_check_unhealthy_threshold)s;")

_update_lb_instance = ("INSERT INTO load_balancer_instance_association "
                              "(deleted, load_balancer_id, instance_id) "
                       "VALUES (FALSE, %(load_balancer_id)s, %(instance_id)s) "
                       "ON DUPLICATE KEY UPDATE "
                               "deleted=FALSE;")

_update_lb_http_server_name = ("INSERT INTO http_server_name "
                                       "(deleted, id, load_balancer_id) "
                               "VALUES (FALSE, %(http_server_name)s, "
                                       "%(load_balancer_id)s) "
                               "ON DUPLICATE KEY UPDATE "
                                       "deleted=FALSE;")

def create_lb(*args, **kwargs):
    # TODO(lzyeval): check dup
    cnt = cu.execute(cnt_lb, kwargs)
    lb_cnt = cu.fetchone().get('lb_cnt', 0)
    cnt = cu.execute(select_http_server_names, kwargs)
    acc_http_server_names = map(lambda x: x['id'], cu.fetchall())
    cnt = cu.execute(select_listen_ports, kwargs)
    acc_listen_ports= map(lambda x: x['listen_port'], cu.fetchall())
    if lb_cnt:
        raise Exception('lb already exists')
    hsns = kwargs.get('http_server_names', [])
    for h in hsns:
        if h in acc_http_server_names:
            raise Exception('%s server name already exists' % h)
    lp = kwargs.get('listen_port')
    if lp in acc_listen_ports:
        raise Exception('%s port already exists' % lp)
    else:
        cnt = cu.execute(hard_delete_lb_config, kwargs)
        db.commit()
        update_lb_config(*args, **kwargs)
        update_lb_instances(*args, **kwargs)
        update_lb_http_server_names(*args, **kwargs)
    instance_ips = list()
    for uuid in kwargs.get('instance_uuids', []):
        cnt = cu.execute(select_fixed_ips, uuid)
        ips = cu.fetchall()
        instance_ips.extend(ips)
    if instance_ips:
        kwargs['instance_ips'] = instance_ips
    return kwargs

def read_lb(*args, **kwargs):
    cnt = cu.execute(select_lb, kwargs)
    lb = cu.fetchone()
    cnt = cu.execute(select_lb_instances, kwargs)
    uuids = cu.fetchall()
    lb['instance_uuids'] = map(lambda x: x['uuid'], uuids)
    if lb['protocol'] == 'http':
        cnt = cu.execute(select_lb_servernames, kwargs)
        server_names = cu.fetchall()
        lb['http_server_names'] = map(lambda x: x['id'], server_names)
    return lb

def read_lb_list(*args, **kwargs):
    cnt = cu.execute(select_lb_list, kwargs)
    lb_list = cu.fetchall()
    return {"load_balancer_list": lb_list,
            "user_name": kwargs.get("user_name"),
            "tenant": kwargs.get("tenant")}

def update_lb_config(*args, **kwargs):
    # TODO(lzyeval): parameter check
    if kwargs.get('protocol') == 'http':
        kwargs['health_check_healthy_threshold'] = 0
        kwargs['health_check_unhealthy_threshold'] = 0
        kwargs['health_check_target_path'] = kwargs.get(
                                             'health_check_target_path',
                                             '/')
        kwargs['health_check_fail_count'] = kwargs.get(
                                            'health_check_fail_count', 0)
    elif kwargs.get('protocol') == 'tcp':
        kwargs['health_check_target_path'] = ""
        kwargs['health_check_fail_count'] = 0
        kwargs['health_check_healthy_threshold'] = kwargs.get(
                              'health_check_healthy_threshold', 2)
        kwargs['health_check_unhealthy_threshold'] = kwargs.get(
                              'health_check_unhealthy_threshold', 10)
    else:
        raise Exception("Invalid protocol")
    cnt = cu.execute(_update_lb_cfg, kwargs)
    db.commit()

def update_lb_instances(*args, **kwargs):
    cnt = cu.execute(delete_instances, kwargs)
    db.commit()
    uuids = kwargs.get('instance_uuids', [])
    cnt = cu.execute(select_instances_by_tenant, kwargs)
    instances = cu.fetchall()
    for i in instances:
        instance_id = i['instance_id']
        instance_uuid = i['uuid']
        if instance_uuid in uuids:
            cnt = cu.execute(_update_lb_instance,
                             {'instance_id': instance_id,
                              'load_balancer_id': kwargs['load_balancer_id']})
    db.commit()


def update_lb_http_server_names(*args, **kwargs):
    cnt = cu.execute(delete_http_server_names, kwargs)
    db.commit()
    https = kwargs.get('http_server_names', [])
    for h in https:
        cnt = cu.execute(_update_lb_http_server_name,
                         {'http_server_name': h,
                          'load_balancer_id': kwargs['load_balancer_id']})
    db.commit()

def delete_lb(*args, **kwargs):
    cnt = cu.execute(delete_lb_config, kwargs)
    cnt = cu.execute(delete_instances, kwargs)
    cnt = cu.execute(delete_http_server_names, kwargs)
    db.commit()
