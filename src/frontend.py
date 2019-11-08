#!/usr/bin/python
''' The Snappy Frontend

   REST commands for:
         Backup  (backup a volume)
         Restore (restore a volume from a backup)
         List    (view details about submitted Snappy jobs)
    are received and processed.

    The frontend interacts with the Snappy Database.

    If Cinder is being backed up, then credientials for the Cinder (Openstack) DB
    are required in the env-snappy-fe.src file.
'''

# Verions:
#     0.5.4:     source_type and source_id are required fields for a Backup request
#     0.5.5:     restore to a different volume feature added
#     0.5.6:     support for S3 target plugin
#     0.5.7:     tablesEditor added
#     0.5.7.1:   "auth_type" added as a field to Tenants local DB
#     0.5.7.2:   authorized checks moved to "authCheck.py"


import authCheck
import sqlite3
import sys
import re
import os
import os.path
import subprocess
import json
import web
import distutils.spawn

URLS = ('/', 'Index',
    '/v2/(.+)/jobs/full', 'FullListV2All',
        '/v2/(.+)/jobs/full/', 'FullListV2All',
        '/v2/(.+)/jobs/full.txt', 'FullListV2All',
        '/v2/(.+)/jobs/full/.txt', 'FullListV2All',
        '/v2/(.+)/jobs/full/(.+)', 'FullListV2Single',
        '/v2/(.+)/jobs/summary', 'SummaryListV2All',
        '/v2/(.+)/jobs/summary/', 'SummaryListV2All',
        '/v2/(.+)/jobs/summary.txt', 'SummaryListV2All',
        '/v2/(.+)/jobs/summary/.txt', 'SummaryListV2All',
        '/v2/(.+)/jobs/summary/(.+)', 'SummaryListV2Single',
        '/v2/(.+)/jobs', 'AddV2',
        '/v2/(.+)/jobs/', 'AddV2',
        '/v2/(.+)/jobs/(.+)', 'RestoreV2')

VERSION = "0.5.7.2"
index_msg = '{"status":"Snappy Frontend is running.  Submit REST commands to use.","version":"' + VERSION  + '"}'

APP = web.application(URLS, globals())

class Index:
    ''' The index URL '''
    def GET(self):
	      return index_msg
    def POST(self):
        return index_msg


def list_main(full_listing, use_json, job_id):
    '''
    There are 8 different options for listing the Snappy DB contents:
    (full/summary) x (JSON/human readable) x (single/all jobs)
    '''
    list_output = ""

    # Full Listings
    if full_listing is True:
        # JSON
        if use_json is True:
            # All
            if job_id == 0:
                list_output = subprocess.check_output("snappy_db_utils/getfulltablejson.py")
            # Single
            else:
                cmd_str = "snappy_db_utils/getsingletablejson.py " + job_id
                list_output = subprocess.check_output(cmd_str.split())
        # Human Readable
        else:
            # All
            if job_id == 0:
                list_output = subprocess.check_output("snappy_db_utils/listall")
            # Single
            else:
                cmd_str = "snappy_db_utils/listsingle " + job_id
                list_output = subprocess.check_output(cmd_str.split())
    #Summary Listing
    else:
        # JSON
        if use_json is True:
            # All
            if job_id == 0:
                list_output = subprocess.check_output("snappy_db_utils/getfullsummaryjson.py")
            # Single
            else:
                cmd_str = "snappy_db_utils/getsinglesummaryjson.py " + job_id
                list_output = subprocess.check_output(cmd_str.split())
        # Human Readable
        else:
            # All
            if job_id == 0:
                list_output = subprocess.check_output("snappy_db_utils/listsummary")

            # Single
            else:
                cmd_str = "snappy_db_utils/listsummarysingle " + job_id
                list_output = subprocess.check_output(cmd_str.split())

    return list_output

def verify_restore_data():
    '''
     Make sure than the POST data was passed in as valid JSON
    and the required data is included:  (restore_type, restore_id)
    '''
    # default values
    restore_type = "abc"
    restore_id = "123456789"
    return_str = '{"status":"input valid"}'

    # Make sure the data is in JSON format
    try:
        item_dict = json.loads(web.data())
    except:
        return_str = '{"status":"ERROR:  valid JSON not found in POST data"}'
        return return_str, restore_type, restore_id

    # Get the restore_type info
    try:
        restore_type = item_dict["restore_type"]
    except KeyError:
        return_str = '{"status":"ERROR:  field <restore_type> not found in POST data"}'
        return return_str, restore_type, restore_id

    # Get the restore_id info
    try:
        restore_id = item_dict["restore_id"]
    except KeyError:
        return_str = '{"status":"ERROR:  <restore_id> not found in POST data"}'
        return return_str, restore_type, restore_id

    return return_str, restore_type, restore_id


def restore_main(tenant_id, job_id):
    ''' Process a RESTORE command  '''
    data = {}

    if "no data" in job_id:
        data['status'] = 'error_msg:  no job_id given'
    elif not isPosInt(job_id):
        data['status'] = 'error_msg:  job_id ' + job_id + ' is not valid'
    else:
        cmd_str = "snappy_db_utils/does_snappy_jobid_exist " + job_id
        job_exists_str = subprocess.check_output(cmd_str.split()).strip()

        if len(job_exists_str) > 0:
            cmd_str = "snappy_db_utils/get_jobtype_from_jobid " + job_id
            jobtype = subprocess.check_output(cmd_str.split()).strip()

            # check to see if Authentication is needed
            # and if so, if the creditials are correct
            auth = web.ctx.env.get('HTTP_AUTHORIZATION')

            if authCheck.is_authorized(tenant_id, auth) is False:
                web.header('WWW-Authenticate', 'Basic realm="Snappy Frontend"')
                web.ctx.status = '401 Unauthorized'
                return '{"status":"ERROR:  Authentication failed for tenant <' + tenant_id + '>"}'

            if "export" in jobtype:
                cmd_str = "snappy_db_utils/get_src_image_from_jobid " + job_id
                image_id = subprocess.check_output(cmd_str.split()).strip()

                ### Restore to a diffrent volume
                if (len(web.data()) > 0):
                    is_valid, restore_type, restore_id = verify_restore_data()
                    if ("input valid" not in is_valid):
                        return is_valid
                    return_str = '{"status":"restore to a different volume"}'

                    # check to see if this restore_type is supported
                    cmd_str = "builder_utils/get_src_id_from_sp_name " + restore_type
                    restore_type_valid = subprocess.check_output(cmd_str.split()).strip()
                    if (len(restore_type_valid) == 0):
                        return '{"status":"error:  restore_type <' + restore_type + '> is not supported"}'

                    # check that the volume <restore_id> exists (the volume we are restoring to)
                    cmd_str = "openstack_db_utils/does_rbd_volume_exist.py " + restore_id
                    id_exists = subprocess.check_output(cmd_str.split())
                    if (id_exists.strip() == "false"):
                        return_txt = '{"status":"ERROR:  Cannot restore to ' + restore_type
                        return_txt += ' volume <' + restore_id + '> since it does not exist"}'
                        return return_txt


                    # get the size of <restore_id> (the volume we are restoring to)
                    cmd_str = "openstack_db_utils/get_rbd_size_in_bytes.py " + restore_id
                    restore_volume_size = subprocess.check_output(cmd_str.split()).strip()

                    # get the allocated size of the backed up volume
                    cmd_str = "snappy_db_utils/get_alloc_size_from_jobid " + job_id
                    alloc_size = subprocess.check_output(cmd_str.split()).strip()

                    # check that the size <restore_id> is >= allocated size
                    if int(restore_volume_size) < int(alloc_size):
                        return_str  = '{"status":"ERROR:  Not enough space.  Backup is ' + alloc_size
                        return_str += ' bytes but volume to restore to is only ' + restore_volume_size + ' bytes."}'
                        return return_str

                    data['restore_to_volume_id'] = restore_id

                    # Restore to a volume that is not the original one
                    cmd_str  = "./restore_to_different_volume "
                    cmd_str += restore_id + " "
                    cmd_str += job_id + " "
                    cmd_str += restore_type

                    new_job_id_str = subprocess.check_output(cmd_str.split())
                
                else:
                    # first make sure that the original volume still exists
                    cmd_str = "openstack_db_utils/does_rbd_volume_exist.py " + image_id
                    rbd_vol_exists = subprocess.check_output(cmd_str.split())

                    if "true" in rbd_vol_exists:
                        # Restore back to the original volume
                        cmd_str = "./restore_to_original_volume " + image_id + " " + job_id
                        new_job_id_str = subprocess.check_output(cmd_str.split())
                    else:

                        return_str  = '{"status":"ERROR:  Request to restore job <' + job_id
                        return_str += '> to the orignal RBD volume <' + image_id
                        return_str += '>, but it does not exist"}'
                        return return_str

                        status_str = 'error_msg:  the RBD volume to restore to <'
                        status_str += image_id + '> does not exist'
                        data['status'] = status_str
                # clean up the output
                new_job_id_str = new_job_id_str.split("\n", 1)[-1].strip("\n")

                data['status'] = 'Restore submitted'
                data['restore_from_job_id'] = job_id
                data['image_id'] = image_id
                data['job_id'] = new_job_id_str
            else:
                status_str = 'error_msg:  job ' + job_id
                status_str += ' is type ' + jobtype
                status_str += '.  It must be an export.'
                data['status'] = status_str

        else:
            data['status'] = 'error_msg:  job ' + job_id + ' does not exist'

    return_txt = json.dumps(data)
    return return_txt

def no_tenant_error(tenant_name):
    return '{"status":"error_msg:  tenant ' + tenant_name + ' does not exist"}'

class RestoreV2:
    '''
    Restore a volume given a backup job_id
    Error cases:  (1) no job_id given
                  (2) job_id doesn't exist
                  (3) job_id isn't an export
    '''
    def POST(self, tenant_id, job_id):
        ''' Restore is a POST command '''
        if does_tenant_exist(tenant_id) is False:
            return no_tenant_error(tenant_id)

        return restore_main(tenant_id, job_id)


# There will be multiple sources that can be backed up as a Ceph RBD volume.
# To do this, we'll need a "layer" that translates from that source's ID
# to the RBD ID that is backing it.
#
# Here we have have:
#     - Cinder Volumes
#     - Kubernetes Persitent Volume Claims
#     - Kubernetes Persistent Volumes
#

def cinder_to_rbd(cinder_id):
    ''' Translate Cinder to RBD  '''
    cmd = "openstack_db_utils/get_rbd_from_cinder " + cinder_id
    rbd_id = subprocess.check_output(cmd.split()).strip("\n")
    
    return rbd_id

def rbd_to_rbd(rbd_id):
    ''' Translate RBD to RBD '''
    return rbd_id

def kubernetes_pv_to_rbd(kubernetes_pv_id):
    ''' Translate Kubernetes PV to RBD '''
    cmd = "./kubernetes_utils/getRBDfromPV.py " + kubernetes_pv_id
    rbd_id = subprocess.check_output(cmd.split()).strip("\n")

    return rbd_id

def kubernetes_pvc_to_pv(kubernetes_pvc_id):
    ''' Translate Kubernetes PVC to PV '''
    cmd = "./kubernetes_utils/getPVfromPVC.py " + kubernetes_pvc_id
    pv_id = subprocess.check_output(cmd.split()).strip("\n")
    return pv_id

def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

def verify_add_data():
    '''
     Make sure than the POST data was passed in as valid JSON
    and the required data is included:  (full_interval, count)
    '''
    # default values
    count = "1"
    full_interval = "604800"     # 1 week
    delta_interval = "0"
    sourcetype = "rbd"
    sourceid = "123456789"
    result = '{"status":"input valid"}'

    # If there's no data passed into this command, we'll catch it here.
    # This can happen if a Restore command was sent but there was
    # no job_id given in the URL, since it'll be interpreted as an Add
    if (len(web.data()) == 0):
        return_str = '{"status":"ERROR:  Data has length 0"}'
        return return_str, "-1", "-1", "-1", "-1", "-1"

    # The data was not in JSON format
    try:
        item_dict = json.loads(web.data())
    except:
        return_str = '{"status":"ERROR:  valid JSON not found in POST data"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval

    # Get the full_interval info
    try:
        full_interval = item_dict["full_interval"]
    except KeyError:
        return_str = '{"status":"ERROR:  field <full_interval> not found in POST data"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval
    if is_int(full_interval) is False or int(full_interval) < 1:
        return_str = '{"status":"ERROR:  <full_interval> is not a positive integer ('+ full_interval +')"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval


    # Get the delta_interval info (this field is not required)
    try:
        delta_interval = item_dict["delta_interval"]
        if is_int(delta_interval) is False or int(delta_interval) < 1:
            return_str = '{"status":"ERROR:  <delta_interval> is not a positive integer ('+ delta_interval +')"}'
            return return_str, sourcetype, sourceid, count, full_interval, delta_interval
    except KeyError:
        pass

    # Get the count info
    try:
        count = item_dict["count"]
    except KeyError:
        return_str = '{"status":"ERROR:  <count> not found in POST data"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval
    if is_int(count) is False or int(count) < 1:
        return_str = '{"status":"ERROR:  <count> is not a positive integer ('+ count  +')"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval


    try:
        sourcetype = item_dict["source_type"]
    except KeyError:
        return_str = '{"status":"ERROR:  <source_type> not found in POST data"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval

    try:
        sourceid = item_dict["source_id"]
    except KeyError:
        return_str = '{"status":"ERROR:  <source_id> not found in POST data"}'
        return return_str, sourcetype, sourceid, count, full_interval, delta_interval

    return result, sourcetype, sourceid, count, full_interval, delta_interval


def does_cmd_exist(cmd):
    '''check to see if a command exists before trying to use it'''
    output = distutils.spawn.find_executable(cmd)
    if output is None:
        return False
    else:
        return True



class AddV2:
    ''' Add a new backup request to the Snappy Database '''
    def POST(self, tenant_id):
        ''' Add is a POST command '''
        if does_tenant_exist(tenant_id) is False:
            return no_tenant_error(tenant_id)

        # Parse the input
        input_verify, original_source_type, original_source_id, count, full_interval, delta_interval = verify_add_data()

        if "ERROR" in input_verify:
            return input_verify

        # check to see if Authentication is needed
        # and if so, if the creditials are correct
        auth = web.ctx.env.get('HTTP_AUTHORIZATION')


        if authCheck.is_authorized(tenant_id, auth) is False:
            web.header('WWW-Authenticate', 'Basic realm="Snappy Frontend"')
            web.ctx.status = '401 Unauthorized'
            return '{"status":"ERROR:  Authentication failed for tenant <' + tenant_id + '>"}'

        data = {}
        source_type = ""
        source_id = ""

        # original_source_type:  what is passed in the REST command
        #          source_type:  what is backed up by Snappy (corresponds to a "source" in the local sqlite DB)
        #
        # Example:  if a Cinder ID is passed in, cinder will be the original_source_type
        #           but rbd could be the source_type, since that is what is actually backed up


        #  the following original_source_type values are currently supported:
        #   -  rbd
        #   -  cinder
        #   -  kpv (Kubernetes Persistent Volume)
        #   -  kpvc Kubernetes Persistent Volume Claim)

        #  the following source_type values are currently supported:
        #   - rbd

        if (original_source_type == "rbd"):
            source_type = original_source_type
            source_id = original_source_id

        elif (original_source_type == "cinder"):
            # find out what Cinder is backed by
            # and what the ID of that backing volume is
            cmd_str="openstack_db_utils/get_cinder_volume_type " + original_source_id
            cinder_backing_type = subprocess.check_output(cmd_str.split()).strip("\n")

            # does this Cinder ID exist
            if len(cinder_backing_type) < 2:
                return '{"status":"Cinder ID <' + original_source_id + '> does not exist"}'
            # is this Cinder ID backed by RBD
            if "rbd" in cinder_backing_type:
                source_type = "rbd"
                source_id = cinder_to_rbd(original_source_id)
# An example of how to add more cinder backing types
#            elif cinder_backing_type == "iscsi":
#                source_type = iscsi
#                source_id = cinder_to_iscsi(original_source_id)
            else:
                return_txt = '{"status":"Cinder ID <' + cid + '> is backed by ' + cinder_backing_type + ', which is not supported'
                if ("Null" or "null" in cinder_backing_type):
                    return_txt += '.  The Cinder volume may have been deleted'
                return_txt += ' "}'

                return return_txt


        elif (original_source_type == "kpv" or original_source_type == "kpvc"):
            # find out what the Kubernetes Persistent Volume (Claim) is backed by
            # and what the ID of that backing volume is

            if does_cmd_exist("kubectl") is False:
                return '{"status":"error_msg:  cmd <kubectl> not found, please submit different source_type (e.g. rbd, cinder)"}'

            if (original_source_type == "kpvc"):
                # check the PVC, if that was passed in

                cmdStr = "kubernetes_utils/doesPVCexist.py " + original_source_id
                pvc_exists = subprocess.check_output(cmdStr.split()).strip("\n")
                if pvc_exists == "True":
                    pv = kubernetes_pvc_to_pv(original_source_id).strip("\n")

                    if len(pv) == 0:
                        return '{"status":"error_msg:  no bound PV found for PVC <' + original_source_id + '>"}'
                else:
                    return '{"status":"error_msg:  Kubernetes PVC <' + original_source_id + '> does not exist"}'

            if (original_source_type == "kpv"):
                kpvid = original_source_id
            else:
                kpvid = pv

            cmdStr = "kubernetes_utils/doesPVexist.py " + kpvid
            pv_exists = subprocess.check_output(cmdStr.split()).strip("\n")

            if pv_exists == "True":
                cmdStr = "kubernetes_utils/isPVbackedbyRBD.py " + kpvid
                backedByRBD = subprocess.check_output(cmdStr.split()).strip("\n")
                if backedByRBD == "True":
                    source_type = "rbd"
                    source_id = kubernetes_pv_to_rbd(kpvid).strip("\n")
                else:
                    return '{"status":"error_msg:  Kubernetes PV <' + kpvid + '> is not backed by RBD"}'
            else:
                return '{"status":"error_msg:  Kubernetes PV <' + kpvid + '> does not exist"}'
        else:
            return '{"status":"error_msg:  source_type <' + original_source_type  + '> not supported"}'

        # Get the source and target profiles associated with this tenant
        src_script = "./builder_utils/get_src_id_from_sp_name"
        tgt_script = "./builder_utils/get_tgt_id_from_tenant_name"
        source_type_num = subprocess.check_output([src_script, source_type]).strip("\n")
        target_type_num = subprocess.check_output([tgt_script, tenant_id]).strip("\n")

        if len(source_type_num) == 0:
            return '{"status":"error_msg:  source type <' + source_type + '> not supported"}'


        if (source_type == "rbd"):
        # Submit a new job to the Snappy Database

            # In cases where we don't have access to the rbd command, we can
            # still submit jobs, but they are not guaranteed to exist.
            # If this happens, the job would result in an error
            # Therefore it is preferred that the frontend has access to the RBD command
            rbd_verified = "false"

            if does_cmd_exist("rbd") is True:
                # If we do have access to the rbd command though, check to see that the volume exists
                cmd = "openstack_db_utils/does_rbd_volume_exist.py " + source_id
                cmd_output = subprocess.check_output(cmd.split())
                if "true" in cmd_output:
                    rbd_verified = "true"
	        elif "unknown" in cmd_output:
		    pass
                else:
                    return '{"status":"error_msg:  rbd volume <' + source_id + '> not found, will not submit backup request"}'



            # compose command to add new backup job
            cmd_str ="./add_rbd_backup_single_scheduled_tenants "
            cmd_str += source_id + " "
            cmd_str += full_interval + " "
            cmd_str += count + " "
            cmd_str += str(source_type_num) + " "
            cmd_str += str(target_type_num) + " "
            cmd_str += original_source_type + " "
            cmd_str += original_source_id

            # execute command
            add_return_txt = subprocess.check_output(cmd_str.split())
            new_id = add_return_txt.split("\n")[-2]

            data['status'] = 'add request for RBD ID <' + source_id + '> submitted'
            data['rbd_verified'] = rbd_verified
            data['job_id'] = new_id
            data['full_interval'] = full_interval
            data['delta_interval'] = delta_interval
            data['count'] = count
        else:
            data['status'] = 'ERROR:  unknown backing source type <' + source_type + '>'

        add_return_txt = json.dumps(data)
        return add_return_txt

def isInt(s):
    ''' is this an integer '''
    try:
        int(s)
        return True
    except ValueError:
        return False

def isPosInt(i):
    ''' is this a positive integer '''
    answer = False
    if isInt(i):
        if int(i) > 0:
            answer = True
    return answer
    
def verify_list_input_v2(job_id):
    ''' Verity that the input is valid for a List Single request '''

    # initial values
    list_output = ""
    is_good = False
    data = {}

    # check to see if the job_id input is valid (is a positive integer)
    if not isPosInt(job_id):
        data['status'] = 'error_msg:  job_id ' + job_id + ' is not valid'
    else:
        # check to see if the job_id exists, which is an error condition
        cmd_str = "snappy_db_utils/does_snappy_jobid_exist " + job_id
        job_exists_str = subprocess.check_output(cmd_str.split()).strip()

        # if there are no errors (the job_id exists if specified), change is_good to True
        # and return the inputs, else return False and an error message.
        if len(job_exists_str) > 0 or "no data" in job_id:
            is_good = True
        else:
            data['status'] ='error_msg:  job_id ' + job_id + ' does not exist'

    list_output = json.dumps(data)

    return is_good, list_output, job_id


def does_tenant_exist(tenant_id):
    ''' Make sure the specified tenant exists '''
    tenant_output = subprocess.check_output(["./builder_utils/get_tenant_info", tenant_id])
    if len(tenant_output) < 5:
        return False
    else:
        return True


class FullListV2All:
    ''' A Full list of all of the jobs in the Snappy DB '''
    def GET(self, tenant_id):
        ''' List is a GET command '''
        if does_tenant_exist(tenant_id) is False:
            return no_tenant_error(tenant_id)
        return list_main(True, ".txt" not in web.ctx.path, 0)

def strip_suffix(string, suffix):
    ''' Strip off a suffix from a string '''
    if string.endswith(suffix):
        return string[:-(len(suffix))]
    else:
        return string

class FullListV2Single:
    ''' A Full list of a single job in the Snappy DB '''
    def GET(self, tenant_id, job_id):
        ''' List is a GET command '''
        if does_tenant_exist(tenant_id) is False:
            return no_tenant_error(tenant_id)

        job_id = strip_suffix(job_id, ".txt")
        is_good, list_output, job_id = verify_list_input_v2(job_id)
        if is_good is True:
            list_output = list_main(True, ".txt" not in web.ctx.path, job_id)

        return list_output

class SummaryListV2All:
    ''' A Summary list of all of the jobs in the Snappy DB '''
    def GET(self, tenant_id):
        ''' List is a GET command '''
        if does_tenant_exist(tenant_id) is False:
            return no_tenant_error(tenant_id)

        return list_main(False, ".txt" not in web.ctx.path, 0)

class SummaryListV2Single:
    ''' A summary list of one job in the Snappy DB '''
    def GET(self, tenant_id, job_id):
        ''' List is a GET command '''
        if does_tenant_exist(tenant_id) is False:
            return no_tenant_error(tenant_id)

        job_id = strip_suffix(job_id, ".txt")
        is_good, list_output, job_id = verify_list_input_v2(job_id)

        if is_good is True:
            list_output = list_main(False, ".txt" not in web.ctx.path, job_id)

        return list_output


def main():
    ''' main '''
    web.internalerror = web.debugerror
    APP.run()

if __name__ == "__main__":
    print("Snappy Frontend version " + VERSION)

    # delete previous file for local Tables (default:  "frontendTables.db")
    db_filename = os.environ['FRONTEND_DB_FILENAME']
    try:
        print("Removing old local DB file " + db_filename)
        os.remove(db_filename)
    except:
        print("The file " + db_filename + " did not exist")
        pass

    # start the sqLite database with the definitions set in the SQL dump file (default:  "frontendTables.sql")
    #
    #  Bash equivalent:        sqlite3 frontendTables.db < frontendTables.sql
    #
    db_conn = sqlite3.connect(db_filename)
    db_sql_filename = os.environ['FRONTEND_DB_SQL_FILENAME']
    try:
        print("Trying to read from file   " + db_sql_filename)
        fd = open(db_sql_filename, 'r')
        c = db_conn.cursor()
        script = fd.read()
        c.executescript(script)
        db_conn.close()
        fd.close()
    except Exception as e:
        print("Exception:  " + str(e))
        print("Could not read file  " + db_sql_filename)
        print("Please check the value of FRONTEND_DB_SQL_FILENAME in file <env-snappy-fe.src>")
	print("")
        print("Exiting...")
        sys.exit(1)
    print("Created new local DB file  " + db_filename)

    main()
