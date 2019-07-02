#!/usr/bin/python

from contextlib import closing
from datetime import datetime
import json
import MySQLdb
import sys
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
    cursor.execute('select * from {}'.format(table))
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def dump_date(thing):
    if isinstance(thing, datetime):
        return thing.isoformat()
    return str(thing)

if len(sys.argv) <> 2:
    print "Usage:  ./getsingletablejson.py <job_id>"
    sys.exit()

with closing(MySQLdb.connect(user=DB_USER, passwd=DB_PASS, db=DB_NAME, host=DB_IP, port=DB_PORT)) as conn, closing(conn.cursor()) as cursor:

    jobid = sys.argv[1]

    dump = {}
    for table in get_tables(cursor):
        dump[table] = get_rows_as_dicts(cursor, table)


    # the default output is if the job isn't found
    data = {}
    data['error_msg'] = 'job id ' + jobid + ' not found'
    result = data

    counter = 0

    while (counter < len(dump["jobs"])):
        if (int(jobid) == dump["jobs"][counter]["id"]):
            result = dump["jobs"][counter]
        counter += 1

    print(json.dumps(result))
