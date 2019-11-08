#!/bin/python

import sqlite3
import os
import re

def is_authorized(tenant_id, auth):
    '''does this request pass Authentication'''
    answer = False

    tenant_auth_type = get_tenant_auth_type(tenant_id)

    if "None" in tenant_auth_type:
        answer = is_authorized_none(tenant_id, auth)
    elif "Basic" in tenant_auth_type:
        answer = is_authorized_basic(tenant_id, auth)
    elif "Token" in tenant_auth_type:
        answer = is_authorized_token(tenant_id, auth)

    return answer

def get_tenant_auth_type(tenant_id):
    # get the PW stored in the local frontend database
    conn = sqlite3.connect(os.environ['FRONTEND_DB_FILENAME'])
    cursor = conn.cursor()
    sqlite3cmd = 'SELECT auth_type FROM tenants WHERE name="' + tenant_id + '";'
    cursor.execute(sqlite3cmd)
    server_key = cursor.fetchone()[0]

    return server_key

def get_request_auth_type(auth):
    ''' Get the authorization type submitted in the request '''
    answer = "none"
    authStr = str(auth)
    if "Basic" in authStr:
        answer = "basic"
    elif "Bearer" in authStr:
        answer = "bearer"
    elif "Token" in authStr:
        answer = "token"
    elif "OAuth" in authStr:
        answer = oauth

    return answer

def get_tenant_pw(tenant_id):
    # get the PW stored in the local frontend database
    conn = sqlite3.connect(os.environ['FRONTEND_DB_FILENAME'])
    cursor = conn.cursor()
    sqlite3cmd = 'SELECT password FROM tenants WHERE name="' + tenant_id + '";'
    cursor.execute(sqlite3cmd)
    server_key = cursor.fetchone()[0]

    return server_key

def is_authorized_token(tenant_id, auth):
    ''' This funcationality not yet implemented '''
    answer = False
    return answer

def is_authorized_none(tenant_id, auth):
    ''' You are always authorized to use this kind of authentication  '''
    return True

def is_authorized_basic(tenant_id, auth):
    '''check to see if this request passes Basic Authentication'''
    answer = False

    # what is the real PW?
    server_key = get_tenant_pw(tenant_id)

    # what is the PW that was passed in by the client?
    try:
       client_key = re.sub('^Basic ', '', auth).strip("\n")

       # if they match, we pass authentication
       if client_key == server_key:
           answer = True
    except:
        # there was a syntax error in the Basic Authentication
        # request, so it will not be authorized
        pass

    return answer
