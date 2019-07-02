#!/usr/bin/python
import subprocess
from subprocess import Popen, PIPE
import sys

rbd_volume = sys.argv[1]

cmd_str = "rbd info " + rbd_volume
output = subprocess.check_output(cmd_str.split())

number = 0
answer = 0
marker = ""

for line in output.split("\n"):
    if "size" in line:
	count = 0
        line = line.strip()
        for word in line.split(" "):
   	    if count == 1:
                number = word
            if count == 2:
                marker = word
            count += 1

if "KB" or "kB" in marker:
    answer = int(number) * 1024
if "MB" in marker:
    answer = int(number) * 1024 * 1024
if "GB" in marker:
    answer = int(number) * 1024 * 1024 * 1024
if "TB" in marker:
    answer = int(number) * 1024 * 1024 * 1024 * 1024

print str(answer)

