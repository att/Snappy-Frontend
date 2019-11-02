#!/bin/python

import json
import sys

def main(filename):

    data = {}

    with open(filename) as json_file:
        data = json.load(json_file)
        json_file.close()


#    db_txt = "BEGIN TRANSACTION;\n"
    db_txt = ""

    # sources
    db_txt += "CREATE TABLE sources ( source_name text, sp_id text, sp_name text, sp_ver text, sp_param text);\n"

    for s in data['sources']:
        v1 = "'" + str(s['source_name']) + "'"
        v2 = "'" + str(s['sp_id']) + "'"
        v3 = "'" + str(s['sp_name']) + "'"
        v4 = "'" + str(s['sp_ver']) + "'"
        v5 = "'" + json.dumps(s['sp_param']) + "'"
        values = "VALUES(" + v1 + "," + v2 + "," + v3 + "," + v4 + "," + v5 + ");"
	db_txt += 'INSERT INTO "sources" ' + values + "\n"


    # targets
    db_txt += "CREATE TABLE targets ( target_name text, tp_id text, tp_name text, tp_ver text, tp_param text);\n"

    for t in data['targets']:
        v1 = "'" + str(t['target_name']) + "'"
        v2 = "'" + str(t['tp_id']) + "'"
        v3 = "'" + str(t['tp_name']) + "'"
        v4 = "'" + str(t['tp_ver']) + "'"
        v5 = "'" + json.dumps(t['tp_param']) + "'"
        values = "VALUES(" + v1 + "," + v2 + "," + v3 + "," + v4 + "," + v5 + ");"
        db_txt += 'INSERT INTO "targets" ' + values + "\n"


    # tenants
    db_txt += "CREATE TABLE tenants ( name text, auth_type text, password text, target_name text);\n"

    for t in data['tenants']:
        v1 = "'" + str(t['name']) + "'"
        v2 = "'" + str(t['auth_type']) + "'"
        v3 = "'" + str(t['password']) + "'"
        v4 = "'" + str(t['target_name']) + "'"
        values = "VALUES(" + v1 + "," + v2 + "," + v3 + "," + v4 + ");"
        db_txt += 'INSERT INTO "tenants" ' + values + "\n"

    return db_txt


if __name__ == "__main__":
    filename = ""

    if len(sys.argv) != 2:
        print("Usage:  tablesJsonToSql <filename.json>")
        sys.exit(1)
    else:
        filename = sys.argv[1]

    print(main(filename))
