#!/usr/bin/python

import subprocess
import sys
import json

def main():
    if (len(sys.argv) != 2):
            print "Usage:  ./getPVfromPVC.py <kubernetes PVC>"
            sys.exit(0)

    targetPVC = sys.argv[1]
    cmd="kubectl get pv -o json --all-namespaces"
    pv_json_string = subprocess.check_output(cmd.split())


    item_dict = json.loads(pv_json_string)

    for i in item_dict["items"]:
        if (i["spec"]["claimRef"]["name"] == targetPVC):
            pvID = i["metadata"]["name"]
            print(pvID)


if __name__ == '__main__':
    main()
