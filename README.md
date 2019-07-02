# Snappy-Frontend
A frontend to use with Snappy (a backup and restore framework).

The frontend will accept REST commands for 3 types of operations:
	- Backup
	- Restore
	- List



Before running, make sure the env-snappy-fe.src file has been filled out and sourced.
        source env-snappy-fe.src

The local Sqlite database should must be filled out with sources, targets and tenants.
This can be done in a number of way, including:
        1.  create a JSON file (via a script or hand-written), then convert to an sql file by running <tablesJsonToSql.py>
        2.  run "python tablesEditor.py [file.json]" to fill out the tables through command line prompts
                (* Recommended *)

Required libraries:
        apt-get update
        apt-get install python
        apt-get install sqlite3
        apt-get install python-mysqldb
        apt-get install mysql-client
        apt-get install jq

        pip install web.py
                
        If "pip" is not installed:
                apt-get install wget
                wget https://bootstrap.pypa.io/get-pip.py
                python get-pip.py


To run:
     python frontend.py <port>

For example, to run on port 8888:
     Short term (foreground):        python frontend.py 8888
     Long  term (background):  nohup python frontend.py 8888 &
