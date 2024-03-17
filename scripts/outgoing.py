#!/usr/bin/env python

import sys

def get_hardware():
    import platform, subprocess, re

    result = ''
    match platform.system():
        case "Windows":
            pass
        case "Darwin":
            pass
        case "Linux":
            cpuinfo = subprocess.check_output("cat /proc/cpuinfo", shell=True).decode("utf-8")
            if "Hardware\t: BCM2835" in cpuinfo:
                for rev in re.findall("Revision\t: (?P<revision>[a-f0-9]+)", cpuinfo):
                    result += f" h{rev}"
            else:
                print(cpuinfo)
        case _:
            pass

    return result



for line in sys.stdin:
    if "CPU:" in line:
        line += get_hardware()
    else:
        sys.stderr.write(f"Laangweilig: {line}")

    sys.stderr.write(f"APRS <- {line}")
    sys.stderr.flush()

    sys.stdout.write(line)
    sys.stdout.flush()
