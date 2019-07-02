#!/usr/bin/python

import subprocess
import sys
import json

def main():
    if (len(sys.argv) != 2):
            print "Usage:  ./doesPVCexist.py <kubernetes PV>"
            sys.exit(0)

    targetPVC = sys.argv[1]
    cmd="kubectl get pvc -o json --all-namespaces"
    pv_json_string = subprocess.check_output(cmd.split())


    item_dict = json.loads(pv_json_string)

    found = "False"

    for i in item_dict["items"]:
#	print("found: <" + i["metadata"]["name"]  + ">")
#	print("match: <"+ targetPVC +">")
#	print("---")
	if (i["metadata"]["name"] == targetPVC):
            found = "True"
            break;

    print(found)

if __name__ == '__main__':
    main()
