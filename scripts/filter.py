#!/usr/bin/env python3

"""
WoW DBC Data Filter
Handles filtering of World of Warcraft DBC data.
"""

from argparse import ArgumentParser
import datetime
from pathlib import Path
import subprocess
from typing import List
from pydantic import BaseModel

# Constants
PYTHON_PATH = Path("C:/Users/joshu/AppData/Local/Programs/Python/Python313/python.exe")

class TaskConfig(BaseModel):
    """Task configuration model."""
    dbfiles: List[str]
    parsers: List[str]
    filters: List[str]
    tasks: List[dict]

def get_wow_version(scripts_dir: Path, cdn_dir: Path) -> str:
    """Get WoW version using wowVersion tool."""
    version_path = scripts_dir / 'tools' / 'wowVersion.py'
    proc = subprocess.run(
        [PYTHON_PATH, version_path, f'--cdnDirPath={cdn_dir}'],
        capture_output=True,
        text=True,
        check=True
    )
    return proc.stdout.strip()

def run_filters(scripts_dir: Path, tasks: TaskConfig):
    """Run all data filters."""
    filters_dir = scripts_dir / 'filters'
    for filter_name in tasks.filters:
        print(f'Filtering {filter_name}...')
        subprocess.run(
            [PYTHON_PATH, f'{filter_name}.py'],
            cwd=filters_dir,
            check=True
        )

def update_lua_meta(scripts_dir: Path, start_time: int, version: str):
    """Update Lua metadata."""
    meta_path = scripts_dir / 'tools' / 'luaMeta.py'
    subprocess.run(
        [
            PYTHON_PATH,
            meta_path,
            f'--mtime={start_time}',
            f'--version={version}'
        ],
        cwd=scripts_dir / 'tools',
        check=True
    )

def main():
    """Main execution function."""
    start_time = int(datetime.datetime.now().timestamp())
    
    # Initialize paths
    scripts_dir = Path(__file__).parent
    cdn_dir = scripts_dir / 'CDN'
    
    try:
        # Load task configuration
        with open(scripts_dir / 'tasks.json') as f:
            tasks = TaskConfig.parse_raw(f.read())
        
        # Get WoW version
        version = get_wow_version(scripts_dir, cdn_dir)
        print(f'Using WoW version: {version}')
        
        # Run filters
        print('Processing filters...')
        run_filters(scripts_dir, tasks)
        
        # Update metadata
        update_lua_meta(scripts_dir, start_time, version)
        
        print('Data filtering completed successfully.')
        
    except subprocess.CalledProcessError as e:
        print(f'Error during filtering: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise

if __name__ == '__main__':
    main()
