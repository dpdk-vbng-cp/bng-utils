#!/usr/bin/env python

import sys
import json
import redis
import socket
import argparse
import telnetlib
import traceback

CONFIG = dict()
CONFIG['debug'] = False
CONFIG['redis_host'] = '127.0.0.1'
CONFIG['redis_port'] = 6379
CONFIG['redis_channel'] = 'accel-ppp'
CONFIG['telnet_host_uplink'] = '127.0.0.1'
CONFIG['telnet_port_uplink'] = 8086
CONFIG['telnet_host_downlink'] = '127.0.0.1'
CONFIG['telnet_port_downlink'] = 8087


def main():
    """ """
    parser = argparse.ArgumentParser(description="A little bit of glue for connecting accel-ppp and DPDK's ip-pipeline.")
    parser.add_argument('--debug', help='enable debug information (default={})'.format(CONFIG['debug']), dest='debug', action='store_true')
    parser.add_argument('--redis-host', help='redis host (default={})'.format(CONFIG['redis_host']), action='store', default=CONFIG['redis_host'], type=str)
    parser.add_argument('--redis-port', help='redis port (default={})'.format(CONFIG['redis_port']), action='store', default=CONFIG['redis_port'], type=int)
    parser.add_argument('--redis-channel', help='redis channel (default={})'.format(CONFIG['redis_channel']), action='store', default=CONFIG['redis_channel'], type=str)
    parser.add_argument('--telnet-host-uplink', help='telnet host uplink (default={})'.format(CONFIG['telnet_host_uplink']), action='store', default=CONFIG['telnet_host_uplink'], type=str)
    parser.add_argument('--telnet-port-uplink', help='telnet port uplink (default={})'.format(CONFIG['telnet_port_uplink']), action='store', default=CONFIG['telnet_port_uplink'], type=int)
    parser.add_argument('--telnet-host-downlink', help='telnet host downlink (default={})'.format(CONFIG['telnet_host_downlink']), action='store', default=CONFIG['telnet_host_downlink'], type=str)
    parser.add_argument('--telnet-port-downlink', help='telnet port downlink (default={})'.format(CONFIG['telnet_port_downlink']), action='store', default=CONFIG['telnet_port_downlink'], type=int)
    p = parser.parse_args(sys.argv[1:])

    CONFIG['debug'] = p.debug
    CONFIG['redis_host'] = p.redis_host
    CONFIG['redis_port'] = p.redis_port
    CONFIG['redis_channel'] = p.redis_channel
    CONFIG['telnet_host_uplink'] = p.telnet_host_uplink
    CONFIG['telnet_port_uplink'] = p.telnet_port_uplink
    CONFIG['telnet_host_downlink'] = p.telnet_host_downlink
    CONFIG['telnet_port_downlink'] = p.telnet_port_downlink

    # redis
    #
    redis_client = redis.StrictRedis(host=CONFIG['redis_host'], port=CONFIG['redis_port'], db=0)
    redis_sub = redis_client.pubsub()

    redis_sub.subscribe(CONFIG['redis_channel'])

    tn = dict()
    for direction in ('uplink', 'downlink', ):
        try:
            tn[direction] = telnetlib.Telnet(CONFIG['telnet_host_{}'.format(direction)], CONFIG['telnet_port_{}'.format(direction)])
        except socket.error, e:
            print traceback.print_exc()

    keep_running = True
    while keep_running:
        try:
            for item in redis_sub.listen():
                d = json.loads(str(item.get('data', {})))
                print d
                # do something with the dictionary d, e.g., talk to the telnet server reachable via tn
                # example:
                # {u'username': u'52:54:00:8e:1d:2c', 
                #  u'calling_station_id': u'52:54:00:8e:1d:2c', 
                #  u'called_station_id': u'acbridge', 
                #  u'ip_addr': u'172.18.10.12', 
                #  u'name': u'ipoe', 
                #  u'session_id': u'e2a53300dd5b30b2', 
                #  u'ctrl_type': u'ipoe', 
                #  u'channel_name': u'52:54:00:8e:1d:2c', 
                #  u'event': u'session-acct-start'}

        except KeyboardInterrupt, e:
            print("done.")
            keep_running = False
        except:
            if CONFIG['debug']:
                print traceback.print_exc()
            raise

 
if __name__ == "__main__":
    main()
