#!/usr/bin/env python

import threading

import MySQLdb
import MySQLdb.cursors

rlock = threading.RLock()

db = MySQLdb.connect(host="localhost", passwd="passwd",
                   user="nova", db="nova",
                   cursorclass=MySQLdb.cursors.DictCursor) 
cu = db.cursor()

select_max_port = ("SELECT MAX(listen_port)+1 as max_port FROM load_balancer "
                   "WHERE deleted is FALSE "
                       "AND listen_port > 10000;")

select_max_del_port = ("SELECT MAX(listen_port) as max_del_port "
                       "FROM load_balancer "
                       "WHERE deleted is TRUE "
                           "AND listen_port > 10000;")

select_http_server_names = ("SELECT id FROM http_server_name "
                            "WHERE deleted is FALSE;")

select_lb = ("SELECT deleted, user_id as user_name, project_id as tenant, "
                    "id as load_balancer_id, protocol, "
                    "listen_port, instance_port, balancing_method, "
                    "health_check_timeout_ms, health_check_interval_ms, "
                    "health_check_target_path, health_check_fail_count, "
                    "health_check_healthy_threshold, "
                    "health_check_unhealthy_threshold "
             "FROM load_balancer lb "
             #"WHERE deleted is FALSE "
                     #"AND user_id=%(user_name)s "
                     "WHERE user_id=%(user_name)s "
                     "AND project_id=%(tenant)s "
                     "AND id=%(load_balancer_id)s;")

select_lb_list = ("SELECT id as load_balancer_id, protocol, listen_port, "
                               "instance_port "
                  "FROM load_balancer "
                  "WHERE deleted is FALSE "
                        "AND user_id=%(user_name)s "
                        "AND project_id=%(tenant)s;")

select_lb_ids = ("SELECT id as load_balacer_id FROM load_balancer "
                 "WHERE deleted is FALSE "
                         "AND id=%(load_balancer_id)s")

cnt_lb = ("SELECT COUNT(*) as lb_cnt FROM load_balancer "
          "WHERE deleted is FALSE "
                  "AND id=%(load_balancer_id)s")

hard_delete_lb_config = ("DELETE FROM load_balancer "
                         "WHERE id=%(load_balancer_id)s;")

delete_lb_config = ("UPDATE load_balancer SET deleted=True "
             "WHERE id=%(load_balancer_id)s;")

delete_instances = ("UPDATE load_balancer_instance_association "
                    "SET deleted=True "
                    "WHERE load_balancer_id=%(load_balancer_id)s;")

delete_http_server_names = ("UPDATE http_server_name SET deleted=True "
                            "WHERE load_balancer_id=%(load_balancer_id)s;")

select_fixed_ips = ("SELECT j.address FROM instances i, fixed_ips j "
                    "WHERE i.deleted is FALSE "
                            "AND i.id=j.instance_id "
                            "AND i.uuid=%s;")

select_lb_instances = ("SELECT i.uuid FROM instances i,"
                               "load_balancer_instance_association a "
                       "WHERE i.deleted is FALSE "
                               "AND a.deleted is FALSE "
                               "AND i.id=a.instance_id "
                               "AND a.load_balancer_id=%(load_balancer_id)s;")

select_lb_servernames = ("SELECT id FROM http_server_name "
                         "WHERE deleted is FALSE "
                                 "AND load_balancer_id=%(load_balancer_id)s")

select_instance_by_uuid = ("SELECT id AS instance_id "
                              "FROM instances "
                              "WHERE deleted=FALSE "
                                      "AND uuid=%(instance_uuid)s;")

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
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'instance_port',
        'balancing_method',
        'health_check_timeout_ms',
        'health_check_interval_ms',
        'health_check_target_path',
        'health_check_fail_count',
        'health_check_healthy_threshold',
        'health_check_unhealthy_threshold',
        'instance_uuids',
        'http_server_names'
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(cnt_lb, kwargs)
    lb_cnt = cu.fetchone().get('lb_cnt', 0)
    if lb_cnt:
        raise Exception('Load balancer name already exists')
    cnt = cu.execute(hard_delete_lb_config, kwargs)
    db.commit()

    if kwargs['instance_port'] < 1 or kwargs['instance_port'] > 65535:
        raise Exception("Instance port out of range")
    with rlock:
        protocol = kwargs['protocol']
        if protocol == "tcp":
            _x = kwargs['health_check_healthy_threshold']
            _y = kwargs['health_check_unhealthy_threshold']
            if _x < 1 or _x > 10:
                raise Exception("Healthy threshold out of range")
            elif _y < 1 or _y > 10:
                raise Exception("Unhealthy threshold out of range")
            listen_port = allocate_listen_port()
            if listen_port > 65535:
                raise Exception("Max listen port exceeded")
            kwargs['listen_port'] = listen_port
        elif protocol == "http":
            kwargs['listen_port'] = 80
            hsns = filter(lambda x: x, map(lambda y: y.strip(),
                                           kwargs.get('http_server_names',
                                                      [])))
            if not hsns:
                raise Exception('HTTP server name absent' % h)
            kwargs['http_server_names'] = hsns
            cnt = cu.execute(select_http_server_names, kwargs)
            acc_http_server_names = map(lambda x: x['id'], cu.fetchall())
            for h in hsns:
                if h in acc_http_server_names:
                    raise Exception('%s server name already exists' % h)
        else:
            raise Exception("Invalid protocol")
        update_lb_config(*args, **kwargs)
    if protocol == "http":
        update_lb_http_server_names(*args, **kwargs)
    update_lb_instances(*args, **kwargs)

def read_lb(allow_deleted=False, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(select_lb, kwargs)
    lb = cu.fetchone()
    if not allow_deleted and lb['deleted']:
        raise Exception("Load balancer does not exist")
    cnt = cu.execute(select_lb_instances, kwargs)
    uuids = cu.fetchall()
    lb['instance_uuids'] = map(lambda x: x['uuid'], uuids)
    if lb['protocol'] == 'http':
        cnt = cu.execute(select_lb_servernames, kwargs)
        server_names = cu.fetchall()
        lb['http_server_names'] = map(lambda x: x['id'], server_names)
    else:
        lb['http_server_names'] = []
    return lb

def read_lb_list(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(select_lb_list, kwargs)
    lb_list = cu.fetchall()
    return {"load_balancer_list": lb_list,
            "user_name": kwargs.get("user_name"),
            "tenant": kwargs.get("tenant")}

def update_lb_config(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'balancing_method',
        'health_check_timeout_ms',
        'health_check_interval_ms',
        'health_check_target_path',
        'health_check_fail_count',
        'health_check_healthy_threshold',
        'health_check_unhealthy_threshold',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    if kwargs.get('balancing_method') not in ["round_robin", "source_binding"]:
        raise Exception("Invalid balancing method")
    if kwargs.get('listen_port') is None:
        lb_info = read_lb(*args, **kwargs)
        kwargs['listen_port'] = lb_info['listen_port']
        kwargs['instance_port'] = lb_info['instance_port']
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
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'instance_uuids',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(delete_instances, kwargs)
    db.commit()
    uuids = kwargs.get('instance_uuids', [])
    for uuid in uuids:
        cnt = cu.execute(select_instance_by_uuid, {'instance_uuid': uuid})
        asdf = cu.fetchone().get("instance_id")
        if asdf is not None:
            cnt = cu.execute(_update_lb_instance,
                             {'instance_id': asdf,
                              'load_balancer_id': kwargs['load_balancer_id']})
    db.commit()


def update_lb_http_server_names(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'http_server_names',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    protocol = kwargs['protocol']
    if protocol != "http":
        return
    cnt = cu.execute(select_http_server_names, kwargs)
    acc_http_server_names = map(lambda x: x['id'], cu.fetchall())
    cnt = cu.execute(select_lb_servernames, kwargs)
    bcc_http_server_names = map(lambda x: x['id'], cu.fetchall())
    acc_http_server_names = filter(lambda x: x not in bcc_http_server_names,
                                                      acc_http_server_names)
    hsns = kwargs.get('http_server_names', [])
    for h in hsns:
        if h in acc_http_server_names:
            raise Exception('%s server name already exists' % h)
    cnt = cu.execute(delete_http_server_names, kwargs)
    db.commit()
    https = kwargs.get('http_server_names', [])
    for h in https:
        cnt = cu.execute(_update_lb_http_server_name,
                         {'http_server_name': h,
                          'load_balancer_id': kwargs['load_balancer_id']})
    db.commit()

def delete_lb(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(delete_lb_config, kwargs)
    cnt = cu.execute(delete_instances, kwargs)
    cnt = cu.execute(delete_http_server_names, kwargs)
    db.commit()

def read_whole_lb(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    lb_info = read_lb(allow_deleted=True, **kwargs)
    instance_ips = list()
    for uuid in lb_info.get('instance_uuids', []):
        cnt = cu.execute(select_fixed_ips, uuid)
        ips = cu.fetchall()
        instance_ips.extend(map(lambda x: x['address'], ips))
    lb_info['instance_ips'] = instance_ips
    return lb_info

def allocate_listen_port():
    cnt = cu.execute(select_max_port)
    res = cu.fetchone()
    if res:
        max_port = res['max_port']
    else:
        max_port = 10000
    cnt = cu.execute(select_max_del_port)
    res = cu.fetchone()
    if res:
        max_del_port = res['max_del_port']
    else:
        max_port = 65535
    return min(max_port, max_del_port)

def read_load_balancer_id_all(*args, **kwargs):
    cnt = cu.execute(select_lb_ids, kwargs)
    return {"load_balancer_ids": map(lambda x: x['load_balancer_id'],
                                     cu.fetchall())}

def read_http_server_name_all(*args, **kwargs):
    cnt = cu.execute(select_http_server_names, kwargs)
    return {"http_server_names": map(lambda x: x['id'], cu.fetchall())}
