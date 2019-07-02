#!/usr/bin/python

import subprocess
import sys
import json

def main():
    if (len(sys.argv) != 2):
            print "Usage:  ./isPVbackedbyRBD.py <kubernetes PV>"
            sys.exit(0)

    targetPV = sys.argv[1]
    cmd="kubectl get pv -o json --all-namespaces"
    pv_json_string = subprocess.check_output(cmd.split())


    item_dict = json.loads(pv_json_string)

    found = False

    for pv in item_dict["items"]:
        if (pv["metadata"]["name"] == targetPV):
            for entry in pv["spec"]:
                if entry == "rbd":
                    found = True
                    break;
            break;

    print(found)

if __name__ == '__main__':
    main()
