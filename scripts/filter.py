#!/usr/bin/env python3

from argparse import ArgumentParser
import datetime
import json
import math
import subprocess
import sys
import os
from os import path, chdir, system, getcwd

try:
    import pandas as pd
    import numpy as np
    from slpp import slpp as lua
    from tqdm import tqdm
    import requests
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "pandas", "numpy", "SLPP-23", "tqdm", "requests"])
    import pandas as pd
    import numpy as np
    from slpp import slpp as lua
    from tqdm import tqdm
    import requests

# -- Constants and Configuration --
filterStartTime = math.floor(datetime.datetime.now().timestamp())

topLevelWorkingDir = path.dirname(getcwd())
scriptsDirPath = path.join(topLevelWorkingDir, 'hero-dbc', 'scripts')
cdnDirPath = path.join(scriptsDirPath, 'CDN')
simcDirPath = path.normpath(path.join(topLevelWorkingDir, '../simulationcraft/simc'))

# -- Logging Setup --
def log_progress(message):
    """Log progress with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Load tasks information (from hero-dbc/scripts/tasks.json)
with open(path.join(scriptsDirPath, 'tasks.json')) as tasksFile:
    tasks = json.load(tasksFile)

# -- Version Detection --
log_progress("Detecting WoW version...")
chdir(path.join(scriptsDirPath, 'tools'))
wowVersionProc = subprocess.Popen([f'python3 wowVersion.py --cdnDirPath={cdnDirPath}'], 
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
version = wowVersionProc.communicate()[0].decode().rstrip()
log_progress(f"Detected WoW version: {version}")

# -- Data Processing --
chdir(path.join(scriptsDirPath, 'filters'))
log_progress('Parsing client data from CSV...')

# Process each filter with progress tracking
for filter in tqdm(tasks['filters'], desc="Processing filters"):
    try:
        log_progress(f'Filtering {filter}...')
        result = system(f'python3 {filter}.py')
        if result != 0:
            log_progress(f'Warning: Filter {filter} returned non-zero exit code: {result}')
    except Exception as e:
        log_progress(f'Error processing filter {filter}: {str(e)}')
        continue

# -- Metadata Update --
log_progress('Updating Lua metadata...')
chdir(path.join(scriptsDirPath, 'tools'))
system(f'python3 luaMeta.py --mtime={filterStartTime} --version={version}')

log_progress('Filtering process completed successfully')
