#!/usr/bin/env python

import sys
for line in sys.stdin:
    sys.stderr.write(f"APRS -> {line}")
    sys.stderr.flush()

    sys.stdout.write(line)
    sys.stdout.flush()
