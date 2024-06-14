#!/usr/bin/env python

import sys

def get_raspberry_revision():
    import platform, subprocess, re

    if platform.system() == "Linux":
        cpuinfo = subprocess.check_output("cat /proc/cpuinfo", shell=True).decode("utf-8")
        if "Hardware\t: BCM2835" in cpuinfo:
            if m := re.match(".*Revision\t: (?P<revision>[a-f0-9]+).*", cpuinfo, re.DOTALL):
                return m.group("revision")


for line in sys.stdin:
    if "CPU:" in line:
        if revision := get_raspberry_revision():
            line = f"{line} h{revision}"

    sys.stderr.write(f"APRS <- {line}")
    sys.stderr.flush()

    sys.stdout.write(line)
    sys.stdout.flush()
