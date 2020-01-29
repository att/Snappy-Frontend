#!/bin/python

import json
import sys
import subprocess
import os.path
import tablesJsonToSql

filename = ""

if len(sys.argv) == 1:
    filename = "frontendTables.json"
    print("Will use default filename " + filename)
elif len(sys.argv) == 2:
    filename = sys.argv[1]
    print("Will use filename " + filename)
else:
    print("Usage:  ./tablesEditor.py [filename]")
    sys.exit(1)


def main_menu(filename):
    print("")
    print("+---------------------------------------+")
    print("| Source, Target and Tenent JSON Editor |")
    print("+---------------------------------------+")
    print("")
    print("\tfilename:  " + filename)
    print("")
    print_tables(filename)
    print("")
    print("Menu:")
    print("1:  Add Source")
    print("2:  Add Target")
    print("3:  Add Tenant")
    print("4:  Delete Source")
    print("5:  Delete Target")
    print("6:  Delete Tenant")
    print("7:  Convert JSON to SQL file")
    print("8:  Quit")
    return

def get_menu_selection():
    selection = input("Enter a selection: ")
    return selection

def view_file(filename):
    print(subprocess.check_output(["cat",filename]))
    return

def print_tables(filename):
    data = read_in_json(filename)

    print("")
    print('{:<10}  {:<30}  {:<5}  {:<20} {:<10}  {:<10}'.format("SOURCES","Name","sp_id","sp_name","sp_ver","sp_param"))
    for s in data['sources']:
        sp_param_text = json.dumps(s['sp_param'])
        print('{:<10}  {:<30}  {:<5}  {:<20} {:<10}  {:<10}'.format("", s['source_name'], s['sp_id'], s['sp_name'], s['sp_ver'], sp_param_text))

    print("")
    print("")
    print('{:<10}  {:<30}  {:<5}  {:<10} {:<10}  {:<10}'.format("TARGETS","Name","tp_id","tp_name","tp_ver","tp_param"))
    for t in data['targets']:
        tp_param_text = json.dumps(t['tp_param'])
        print('{:<10}  {:<30}  {:<5}  {:<10} {:<10}  {:<10}'.format("", t['target_name'], t['tp_id'], t['tp_name'], t['tp_ver'],tp_param_text))

    print("")
    print("")
#    print("TENANTS\t\tName\tPassword\tTarget")
    print('{:<10}  {:<30}  {:<30}  {:<30}  {:<30}'.format("TENANTS","Name","Auth_Type","Password","Target"))
    for t in data['tenants']:
#        print("\t\t" + t['name'] + "\t" + t['password'] + "\t" + t['target_name'])
        print('{:<10}  {:<30}  {:<30}  {:<30}  {:<30}'.format("", t['name'], t['auth_type'], t['password'], t['target_name']))

    return


def add_tenant(filename):
    print("")
    print("Add new Tenant")
    print("--------------")

    # get the data needed for the new Tenant
    name = raw_input("Enter Tenant name:")

    # None and Basic is currently supported.  Other types will be added such as Token based authentication
    auth_type = raw_input("Enter Authentication Type (None, Basic):")

    if ("None" in auth_type):
	      password = "N/A"
    elif ("Basic" in auth_type):
	      password = raw_input("Enter Tenant password:")
    else:
        auth_type = "None"
        password = "N/A"

    target_name = raw_input("Enter Tenant Target Name:")

    data = read_in_json(filename)

    # add it to the JSON
    new_entry = {}
    new_entry['name'] = name
    new_entry['auth_type'] = auth_type
    new_entry['password'] = password
    new_entry['target_name'] = target_name

    data["tenants"].append(new_entry)

    remove_and_rewrite(filename, data)
    return

def add_source(filename):
    print("")
    print("Add new Source")
    print("--------------")
    new_entry = {}
    new_sp_entry = {}

    # get the data needed for the new Tenant
    source_name = raw_input("Enter Source name:")
    sp_name = raw_input("Enter Source Plugin (SP) Name.  Choices are (rbd, localdirectory):")
    sp_id = ""
    sp_ver = ""
    if (sp_name == "rbd"):
        sp_id = "0"
        sp_ver = "0.1.0"
        rbd_user = raw_input("Enter RBD (Ceph) username:")
        rbd_mon_host = raw_input("Enter RBD (Ceph) monitor host:")
        rbd_key = raw_input("Enter RBD (Ceph) key:")
        rbd_pool = raw_input("Enter RBD pool:")
        # construct the JSON for the RBD Source Plugin (SP) part
        new_sp_entry['user'] = rbd_user
        new_sp_entry['mon_host'] = rbd_mon_host
        new_sp_entry['key'] = rbd_key
        new_sp_entry['pool'] = rbd_pool
    elif (sp_name == "localdirectory"):
	sp_id = "1002"
	sp_ver = "0.1.0"
        # The localdirectory SP part is empty in this table.
	# The path will be filled in as each backup request is received.
	# (see builder_utils/arg2_builder_localdirectory)
    else:
        print("unknown Source Plugin (SP) " + sp_name)
        sys.exit()

    new_entry['source_name'] = source_name
    new_entry['sp_id'] = sp_id
    new_entry['sp_name'] = sp_name
    new_entry['sp_ver'] = sp_ver
    new_entry['sp_param'] = new_sp_entry

    data = read_in_json(filename)

    # add it to the JSON 
    data["sources"].append(new_entry)

    # delete the old file and write it again
    remove_and_rewrite(filename, data)
    return


def add_target(filename):
    print("")
    print("Add new Target")
    print("--------------")

    new_entry = {}
    new_tp_entry = {}

    # get the data needed for the new Tenant                                                          

    target_name = raw_input("Enter Target name:")
    tp_name = raw_input("Enter Target Plugin (TP) name.  Choices are (swift, s3):")
    tp_id = ""
    tp_ver = ""

    if (tp_name == "swift"):
        tp_id = "1000"
        tp_ver = "0.1.0"
        swift_url = raw_input("Enter Swift endpoint URL:")
        swift_user = raw_input("Enter Swift username:")
        swift_password = raw_input("Enter Swift password:")
        swift_auth_method = "tempauth"
        swift_container = raw_input("Enter Swift container:")
        swift_project = raw_input("Enter Swift project:")
        # construct the JSON for the Target Plugin (TP) part
        new_tp_entry['user'] = swift_user
        new_tp_entry['password'] = swift_password
        new_tp_entry['auth_method'] = swift_auth_method
        new_tp_entry['url'] = swift_url
        new_tp_entry['container'] = swift_container
        new_tp_entry['project'] = swift_project
    elif (tp_name == "s3"):
        tp_id ="1001"
        tp_ver = "0.1.0"
        s3_url = raw_input("Enter S3 endpoint URL:")
        s3_user = raw_input("Enter S3 username:")
        s3_password = raw_input("Enter S3 password:")
        s3_container = raw_input("Enter S3 container:")
        s3_region =raw_input("Enter S3 region:")
        # construct the JSON for the Target Plugin (TP) part                                                   
        new_tp_entry['user'] = s3_user
        new_tp_entry['password'] = s3_password
        new_tp_entry['url'] = s3_url
        new_tp_entry['container'] = s3_container
        new_tp_entry['region'] = s3_region
    else:
        print("unkown Target Plugin (TP) " + tp_name)
        sys.exit()

    # add it to the JSON
    new_entry['target_name'] = target_name
    new_entry['tp_id'] = tp_id
    new_entry['tp_name'] = tp_name
    new_entry['tp_ver'] = tp_ver
    new_entry['tp_param'] = new_tp_entry

    data = read_in_json(filename)

    # add it to the JSON 
    data["targets"].append(new_entry)

    # delete the old file and write it again
    remove_and_rewrite(filename, data)
    return


def delete_source(filename):
    source_name = raw_input("Delete which source (name)?")

    # read in the JSON from the file 
    data = read_in_json(filename)

    # find and delete the entry from the JSON                         
    for s in data['sources']:
        if s['source_name'] == source_name:
            data['sources'].remove(s)

    remove_and_rewrite(filename, data)

    return

def delete_target(filename):
    target_name = raw_input("Delete which target (name)?")
    
    data = read_in_json(filename)

    # find and delete the entry from the JSON                                                                     
    for t in data['targets']:
        if t['target_name'] == target_name:
            data['targets'].remove(t)

    remove_and_rewrite(filename, data)
    return

def delete_tenant(filename):
    tenant_name = raw_input("Delete which tenant (name)?")

    data = read_in_json(filename)

    # find and delete the entry from the JSON
    for t in data['tenants']:
        if t['name'] == tenant_name:
            data['tenants'].remove(t)

    remove_and_rewrite(filename, data)
    return

def read_in_json(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
        json_file.close()

    return data

def remove_and_rewrite(filename, data):
    # delete the old file                                                                         
    subprocess.check_output(["rm",filename])

    # write the new file                                                                                   
    new_file = open(filename, "w")
    new_file.write(json.dumps(data))
    new_file.close()
    return

def convert_to_sql(filename):
    index = filename.rfind(".")
    sql_filename = filename[:index] + ".sql"
    print("Creating file " + sql_filename)
    sql_text = tablesJsonToSql.main(filename)
#    print(sql_text)

    # write the SQL file
    new_file = open(sql_filename, "w")
    new_file.write(sql_text)
    new_file.close()
    return

if not os.path.isfile(filename):
    print("Creating new file...")
    new_file = open(filename, "w")
    new_file.write('{"tenants": [],"sources": [],"targets": []}')
    new_file.close()

while (True):
    main_menu(filename)

    sel = get_menu_selection()

    if (sel == 1):
        add_source(filename)
    elif (sel == 2):
        add_target(filename)
    elif (sel == 3):
        add_tenant(filename)
    elif (sel == 4):
        delete_source(filename)
    elif (sel == 5):
        delete_target(filename)
    elif (sel == 6):
        delete_tenant(filename)
    elif (sel == 7):
        convert_to_sql(filename)
    elif (sel == 8):
        sys.exit(0)
    else:
        print("Unknown selection, please try again.")
