import uuid
from models import *
from utils import *
import re
import json
import pymysql
import pymysql.cursors
import sqlite3
from typing import *
import pandas as pd

# 创建数据集
def create_dataset(name: str) -> str:
    ds  = DataSet(
        uid=uuid.uuid4().hex,
        name=name,
    )
    session.add(ds)
    session.commit()
    return ds.uid

# 删除数据集
def delete_dataset(uid: str):
    ds = session.query(DataSet).filter(DataSet.uid==uid).first()
    check_cond(ds, ERR_NOT_FOUND, f"数据集 [uid={uid}] 不存在")
    session.query(DataSet).filter(DataSet.uid==uid).delete()
    session.query(DataItem).filter(DataItem.dataset_uid==uid).delete()
    session.commit()

# 获取单个数据集
def get_single_dataset(name: str):
    ds = session.query(DataSet).filter(DataSet.name==name).first()
    check_cond(ds, ERR_NOT_FOUND, f"数据集 [name={name}] 不存在")
    return ds

# 获取数据集列表
def get_datasets(page_num=1, page_size=10) -> JsonObj:
    q = session.query(DataSet)
    total = q.count()
    list_ = q.offset((page_num - 1) * page_size).limit(page_size).all()
    return {
        'total': total,
        'list': list_,
    }

# 删除数据项
def delete_dataitem(ds_uid: str, uids: List[str]):
    check_cond(uids, ERR_NOT_FOUND, "UID 不能为零个")
    check_cond(ds_uid, ERR_NOT_FOUND, "数据集 UID 不能为空")
    session.query(DataItem) \
        .filter(DataItem.dataset_uid==ds_uid) \
        .filter(DataItem.uid.in_(uids)).delete()
    session.commit()

# 删除单个数据项
def delete_single_dataitem(uid: str):
    ditem = session.query(DataItem).filter(DataItem.uid==uid).first()
    check_cond(ditem, ERR_NOT_FOUND, f"数据项 [uid={uid}] 不存在")
    session.query(DataItem).filter(DataItem.uid==uid).delete()
    session.commit()

# 添加数据项
def add_dataitem(ds_uid: str, args: JsonObj):
    ds = session.query(DataSet).filter(DataSet.uid==ds_uid).first()
    check_cond(ds, ERR_NOT_FOUND, f"数据集 [uid={ds_uid}] 不存在")
    dit = DataItem(
        dataset_uid=ds_uid,
        uid=uuid.uuid4().hex,
        args=json.dumps(args),
    )
    session.add(dit)
    session.commit()

def update_dataitem(uid: str, args: JsonObj):
    t = session.query(DataItem).filter(DataItem.uid==uid).first()
    check_cond(t, ERR_NOT_FOUND, f'数据项 [uid={uid}] 不存在')
    session.query(DataItem).filter(DataItem.uid==uid).update(dict(
        args=json.dumps(args), 
        ))
    session.commit()

# 获取数据项列表
def get_dataitems(ds_uid: str, page_num=1, page_size=10) -> JsonObj:
    check_cond(ds_uid, ERR_NOT_FOUND, "数据集 UID 不能为空")
    q = session.query(DataItem) \
        .filter(DataItem.dataset_uid==ds_uid)
    total = q.count()
    list_ = q.offset((page_num - 1) * page_size).limit(page_size).all()
    return {
        'total': total,
        'list': list_,
    }

# 字典转换为数据项
def dict2dit(d: pd.DataFrame, uid: str) -> DataItem:
    args = json.dumps(d)
    dit = DataItem(
        uid=uuid.uuid4().hex,
        dataset_uid=uid,
        args=args,
    )
    return dit

# 从 DF 导入数据项
def load_dataitems_from_df(df: pd.DataFrame, uid: str):
    for s in df.iloc:
        dit = dict2dit(s.to_dict(), uid)
        session.add(dit)
    session.commit()

# 从数据库游标导入数据项
def load_dataitems_from_cursor(cur: 'Cursor', tbname: str, uid: str):
    cur.execute("select * from %s", (tbname,))
    rs = cur.fetchall()
    for r in rs:
        dit = dict2dit(r, uid)
        session.add(dit)
    session.commit()

# Sqlite RS 列表转换为字典
def sqlite_dict_factory(cursor: 'Cursor', row: 'ResultSet'):  
    d = {}  
    for idx, col in enumerate(cursor.description):  
        d[col[0]] = row[idx]  
    return d

# 从 Sqlite 导入数据项
def load_dataitems_sqlite(uid: str, dbname: str, table: str):
    ds = session.query(DataSet).filter(DataSet.uid==uid).first()
    check_cond(ds, ERR_NOT_FOUND, "数据集 [uid={uid}] 不存在")
    check_cond(dbname and table, ERR_PARAM_INVALID, "数据库路径、表名不能为空")

    conn = sqlite3.connect(dbname)
    conn.row_factory = sqlite_dict_factory
    cur = conn.cursor()
    load_dataitems_from_cursor(cur, table, uid)
    cur.close()
    conn.close()

# 从 MySQL 导入数据项
def load_dataitems_mysql(uid: str, username: str, password: str, host: str, port: str, dbname: str, table: str, charset='utf8mb4'):
    ds = session.query(DataSet).filter(DataSet.uid==uid).first()
    check_cond(ds, ERR_NOT_FOUND, "数据集 [uid={uid}] 不存在")
    check_cond(username and password and host and port and dbname and table,
        ERR_PARAM_INVALID, "用户名、密码、主机、端口、库名、表名不能为空")

    conn = pymysql.connect(
        user=username, password=password,
        host=host, port=port,
        database=dbname,
        charset=charset,
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    load_dataitems_from_cursor(
        cur, table  , uid)
    cur.close()
    conn.close()


def load_dataitems_csv_excel(dsname: str, fname: str):
    ds = session.query(DataSet).filter(DataSet.name==dsname).first()
    check_cond(ds, ERR_NOT_FOUND, "数据集 [name={dsname}] 不存在")
    extname = fname.split('.')[-1].lower()
    check_cond(
            extname in ['csv', 'xls', 'xlsx'], 
            ERR_PARAM_INVALID, '文件名必须以 CSV/XLS/XLSX 结尾'
    )
 
    df = (
        pd.read_csv(fname) 
        if fname.endswith('.csv') 
        else pd.read_excel(fname)
    )
    load_dataitems_from_df(df, ds.uid)
    

# 从 JSONL 导入数据项
def load_dataitems_jsonl(uid: str, fname: str, ):
    ds = session.query(DataSet).filter(DataSet.uid==uid).first()
    check_cond(ds, ERR_NOT_FOUND, "数据集 [uid={uid}] 不存在")
    check_cond(fname.endswith('.jsonl'), ERR_PARAM_INVALID, '文件名必须以 JSONL 结尾')
    
    lines = open(fname, encoding='utf8').read().split('\n')
    lines = [l for l in lines if l.strip()]
    for l in lines:
        it = json.loads(l)
        dit = DataItem(
            uid=uuid.uuid4().hex,
            dataset_uid=uid,
            args=l,
        )
        session.add(dit)
    session.commit()

# 从 JSON 导入数据项
def load_dataitems_json(uid: str, fname: str, list_prop = '*'):
    ds = session.query(DataSet).filter(DataSet.uid==uid).first()
    check_cond(ds, ERR_NOT_FOUND, "数据集 [uid={uid}] 不存在")
    check_cond(fname.endswith('.json'), ERR_PARAM_INVALID, '文件名必须以 JSON 结尾')
    check_cond(list_prop, ERR_PARAM_INVALID, '数据列表属性不能为空')
    
    j = json.loads(open(fname, encoding='utf8').read())
    li = dict_get_prop(j, list_prop)
    li = reduce(lambda x, y: x + y, li, [])
    for it in li:
        dit = DataItem(
            uid=uuid.uuid4().hex,
            dataset_uid=uid,
            args=json.dumps(it),
        )
        session.add(dit)
    session.commit()

