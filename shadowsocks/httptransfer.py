#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
#import cymysql
import time
import sys
import socket
import config
import json
import urllib
import urllib2


class HttpTransfer(object):

    instance = None

    def __init__(self):
        self.last_get_transfer = {}

    @staticmethod
    def get_instance():
        if HttpTransfer.instance is None:
            HttpTransfer.instance = HttpTransfer()
        return HttpTransfer.instance

    @staticmethod
    def send_command(cmd):
        data = ''
        try:
            cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cli.settimeout(1)
            cli.sendto(cmd, ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
            data, addr = cli.recvfrom(1500)
            cli.close()
            # TODO: bad way solve timed out
            time.sleep(0.05)
        except:
            logging.warn('send_command response')
        return data

    @staticmethod
    def get_servers_transfer():
        dt_transfer = {}
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(2)
        cli.sendto('transfer: {}', ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
        bflag = False
        while True:
            data, addr = cli.recvfrom(1500)
            if data == 'e':
                break
            data = json.loads(data)
            print data
            dt_transfer.update(data)
        cli.close()
        return dt_transfer


    def push_db_all_user(self):
        dt_transfer = self.get_servers_transfer()
        last_time = str(int(time.time()))
        url = "https://shichapie.com/ssnode/traffic_cost"
        post_data = []
        for id in dt_transfer.keys():
            post_data.append(','.join([id, dt_transfer[id], last_time]))
        post_value = {"user_traffic_cost": "|".join(past_data)}
        data = urllib.urlencode(post_value)
        request = urllib2.Request(url, jdata)
        urllib2.urlopen(request)

    @staticmethod
    def pull_db_all_user():
        #从api中获取port u d transfer_enable passwd switch enable
        rows = []
        url = "https://shichapie.com/ssnode/users"
        try:
            response = urllib2.urlopen(url)
            json_result = response.read()
            rows = json.loads(json_result)
        except:
            logging.warn('get users from api') 
        return rows
     
    @staticmethod
    def del_server_out_of_bound_safe(rows):
        for row in rows:
            server = json.loads(HttpTransfer.get_instance().send_command('stat: {"server_port":%s}' % row[0]))
            if server['stat'] != 'ko':
                if row[5] == 0 or row[6] == 0:
                    #stop disable or switch off user
                    logging.info('db stop server at port [%s] reason: disable' % (row[0]))
                    HttpTransfer.send_command('remove: {"server_port":%s}' % row[0])
                elif row[1] + row[2] >= row[3]:
                    #stop out bandwidth user
                    logging.info('db stop server at port [%s] reason: out bandwidth' % (row[0]))
                    HttpTransfer.send_command('remove: {"server_port":%s}' % row[0])
                if server['password'] != row[4]:
                    #password changed
                    logging.info('db stop server at port [%s] reason: password changed' % (row[0]))
                    HttpTransfer.send_command('remove: {"server_port":%s}' % row[0])
            else:
                if row[5] == 1 and row[6] == 1 and row[1] + row[2] < row[3]:
                    logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                    HttpTransfer.send_command('add: {"server_port": %s, "password":"%s"}'% (row[0], row[4]))
                    print('add: {"server_port": %s, "password":"%s"}'% (row[0], row[4]))

    @staticmethod
    def thread_db():
        import socket
        import time
        timeout = 30
        socket.setdefaulttimeout(timeout)
        while True:
            logging.warn('db loop')
            try:
                HttpTransfer.get_instance().push_db_all_user()
                rows = HttpTransfer.get_instance().pull_db_all_user()
                HttpTransfer.del_server_out_of_bound_safe(rows)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.warn('db thread except:%s' % e)
            finally:
                time.sleep(15)

