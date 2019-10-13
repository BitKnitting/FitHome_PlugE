#!/usr/bin/env python3
from plugs_lib import Plugs
import os
import sys
LIB_PATH = os.environ['LIB_PATH']
PROJECT_ID = os.environ['PROJECT_ID']
MONITOR_NAME = os.environ['MONITOR_NAME']

sys.path.append(LIB_PATH)
p = Plugs()

p.start(MONITOR_NAME, PROJECT_ID)
