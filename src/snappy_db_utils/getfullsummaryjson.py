#!/usr/bin/python

from contextlib import closing
from datetime import datetime
import json
import MySQLdb
import os

DB_USER = os.environ["SNAPPY_USER"]
DB_PASS = os.environ["SNAPPY_PW"]
DB_NAME = os.environ["SNAPPY_DB"]
DB_IP = os.environ["SNAPPY_HOST"]
DB_PORT = int(os.environ["SNAPPY_PORT"])

def get_tables(cursor):
    cursor.execute('SHOW tables')
    return [r[0] for r in cursor.fetchall()] 

def get_rows_as_dicts(cursor, table):
    cursor.execute('select id,sub,next,parent,grp,root,state,done,result,feid,policy,arg0,arg1 from {}'.format(table))
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dump_date(thing):
    if isinstance(thing, datetime):
        return thing.isoformat()
    return str(thing)


with closing(MySQLdb.connect(user=DB_USER, passwd=DB_PASS, db=DB_NAME, host=DB_IP, port=DB_PORT)) as conn, closing(conn.cursor()) as cursor:
    dump = {}
    for table in get_tables(cursor):
        dump[table] = get_rows_as_dicts(cursor, table)
    print(json.dumps(dump, default=dump_date, indent=2))

    

