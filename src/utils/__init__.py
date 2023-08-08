from datetime import datetime
from functools import reduce
import traceback
from flask import Flask
import json
from threading import Lock
import psutil
import os
from utils.errors import *
import requests
import config as config
from typing import *

DATETIME_FORMAT_0 = '[%Y-%m-%d %H:%M:%S]'
DATETIME_FORMAT_1 = '%Y-%m-%d %H:%M:%S'
DATETIME_FORMAT_2 = '%Y-%m-%d'
DATETIME_FORMAT_3 = '%Y-%m-%d %H:%M:%S.%f'
DATETIME_FORMAT_4 = '%Y-%m-%dT%H:%M:%S.%fZ'
HTTP_HEADER_CONTENT_TYPE = 'Content-Type'
MIME_JSON = 'application/json'

JsonObj = Dict[str, Any]

def dt2s1(dt):
    return f'{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
    # return dt.strftime(DATETIME_FORMAT_1)

def s2dt1(s):
    return datetime.strptime(s, DATETIME_FORMAT_1)

def loghead():
    return datetime.now().strftime(DATETIME_FORMAT_0)

def log_name(name):
    def outer(f):
        def inner(*args, **kw):
            print(f'{loghead()} {name} start')
            r = f(*args, **kw)
            print(f'{loghead()} {name} end')
            return r
        return inner
    return outer 

def safe(default=None):
    def outer(f):
        def inner(*args, **kw):
            try: return f(*args, **kw)
            except: 
                traceback.print_exc()
                return default
        return inner
    return outer

def with_app_ctx(app):
    def outer(f):
        def inner(*args, **kw):
            nonlocal app
            if hasattr(app, 'app'):
                app = app.app
            with app.app_context(): f(*args, **kw)
        return inner
    return outer

flag_map = {}

def single_trd(default=None):
    def outer(f):
        flag_map[id(f)] = Lock()
        def inner(*args, **kw):
            succ = flag_map[id(f)].acquire(blocking=False)
            if not succ: return default
            try:
                return f(*args, **kw)
            finally:
                flag_map[id(f)].release()
        return inner
    return outer



def ok(data=None):
    return (
        json.dumps({
            'code': ERR_OK,
            'data': data,
        }), 200, {HTTP_HEADER_CONTENT_TYPE: MIME_JSON}
    )

def fail(code=ERR_FAIL, msg='', http_code=400):
    return (
        json.dumps({
            'code': code,
            'msg': msg,
        }), http_code, {HTTP_HEADER_CONTENT_TYPE: MIME_JSON}
    )

def kill_proc_by_port(port):
    netstats = psutil.net_connections('tcp')
    for n in netstats:
        if  n.laddr.port == port and \
            n.status == 'LISTEN':
            os.kill(n.pid, 9)
            print(f'KILL PID: {n.pid}')

def pad_table(table):
    ncol = len(table[0])
    col_widths = [0] * ncol
    for _, row in enumerate(table):
        for j, elem in enumerate(row):
            col_widths[j] = max(col_widths[j], len(elem))
    for i, row in enumerate(table):
        for j, elem in enumerate(row):
            table[i][j] += '\x20' * (col_widths[j] - len(elem))
    return table

def parse_image_name(name):
    return name.split(":")[:2] \
           if ":" in name \
           else (name, 'latest')

def gen_time_diff_str(td):
    diff = int(td.total_seconds())
    if diff < 0: diff = -diff
    day = diff // (60 * 60 * 24)
    hr = diff // (60 * 60) - day * 24
    min = diff // 60 - day * 24 * 60 - hr * 60
    sec = diff - day * 24 * 60 * 60 - hr * 60 * 60 - min * 60
    res = ''
    if day != 0:
        res += f'{day}天'
    if hr != 0:
        res += f'{hr}时'
    if min != 0:
        res += f'{min}分'
    if sec != 0:
        res += f'{sec}秒'
    if res == '':
        res = '0秒'
    return res

def get_page_num_size(args):
    pg_num = int(args.get('page_num', 1))
    pg_size = int(args.get('page_size', 10)) or 0xffffffff
    return pg_num, pg_size

def log_func(f):
    def inner(*args, **kw):
        r = f(*args, **kw)
        print(f'{f.__name__}, args: {args}, kw: {kw}, res: {r}')
        return r
    return inner

if config.log_http:
    requests.get = log_func(requests.get)
    requests.post = log_func(requests.post)

def percent(rate):
    return int(rate * 100)

    
def inter_arr_to_sec(arr):
    return arr[4] + arr[3] * 60 + arr[2] * 3600 + \
           arr[1] * 3600 * 24 + arr[0] * 3600 * 24 * 30

def sec_to_inter_arr(secs):
    return [
        secs // (3600 * 24 * 30),
        secs // (3600 * 24) % 30,
        secs // 3600 % 24,
        secs // 60 % 60,
        secs % 60,
    ]

def dict_get_prop(d, prop):
    res = [d]
    props = prop.split('.')
    for p in props:
        p = p.strip()
        if p == '*':
            res = reduce(lambda x, y: x + y, res, [])
        else:
            res = [it.get(p) for it in res]
    return res