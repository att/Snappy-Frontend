#!/usr/bin/python
import distutils.spawn
import subprocess
from subprocess import Popen, PIPE
import sys

rbd_volume = sys.argv[1]

# the default case:  the "rbd" command exists but can't connect to the cluster
answer = "unknown"
output = ""
error = ""
cmd = "rbd info " + rbd_volume

# we are assuming that the "rbd" command exists
try:
    p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
except subprocess.CalledProcessError as e:
    pass

if "create_timestamp" in output:
    answer = "true"

if "error opening image" in error:
    answer = "false"


print answer

