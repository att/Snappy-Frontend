#!/usr/bin/python

import subprocess
import sys
import json

def main():
    if (len(sys.argv) != 2):
            print "Usage:  ./getPVCfromPV.py <kubernetes PVC>"
            sys.exit(0)

    targetPV = sys.argv[1]
    cmd = "kubectl get pv -o json --all-namespaces"
    pv_json_string = subprocess.check_output(cmd.split())


    item_dict = json.loads(pv_json_string)

    for pv in item_dict["items"]:
        if (pv["metadata"]["name"] == targetPV):
            pvcID = pv["spec"]["claimRef"]["name"]
            print(pvcID)


if __name__ == '__main__':
    main()
