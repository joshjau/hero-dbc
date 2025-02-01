#!/usr/bin/env python3

"""
WoW DBC Data Extractor
Handles extraction and processing of World of Warcraft DBC data.
"""

from argparse import ArgumentParser
import datetime
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd
from pydantic import BaseModel, Field

# Constants
PYTHON_PATH = Path("C:/Users/joshu/AppData/Local/Programs/Python/Python313/python.exe")
SIMC_DIR = Path("C:/Users/joshu/OneDrive/Documents/simc")

class WowRealm(str, Enum):
    """Valid WoW realm types."""
    LIVE = 'live'
    PTR = 'ptr'
    ALPHA = 'alpha'
    BETA = 'beta'

class TaskConfig(BaseModel):
    """Task configuration model."""
    dbfiles: List[str]
    parsers: List[str]
    filters: List[str]
    tasks: List[Dict[str, Any]]

@dataclass
class Paths:
    """Store all relevant paths."""
    root: Path  # hero-dbc root
    scripts: Path
    cdn: Path
    dbc: Path
    simc: Path
    wow: Optional[Path] = None

def setup_argument_parser() -> ArgumentParser:
    """Setup command line argument parser."""
    parser = ArgumentParser(description='WoW DBC Data Extractor')
    parser.add_argument("--wowdir", dest="wow_dir", help="Path to World of Warcraft directory.")
    parser.add_argument(
        "--wowrealm", 
        dest="wow_realm", 
        default=WowRealm.LIVE,
        type=WowRealm,
        choices=list(WowRealm),
        help="World of Warcraft realm type."
    )
    parser.add_argument(
        "--simc",
        action='store_true',
        dest='update_simc',
        default=False,
        help='Update simc data.'
    )
    return parser

def find_wow_directory(scripts_dir: Path) -> Optional[Path]:
    """Find WoW directory using wowDirFinder tool."""
    finder_path = scripts_dir / 'tools' / 'wowDirFinder.py'
    proc = subprocess.run(
        [PYTHON_PATH, finder_path],
        capture_output=True,
        text=True,
        check=True
    )
    result = proc.stdout.strip()
    return Path(result) if result != 'False' else None

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

def extract_cdn_data(paths: Paths, realm: WowRealm):
    """Extract data from CDN using casc_extract."""
    casc_dir = paths.simc / 'casc_extract'
    cmd = [
        PYTHON_PATH,
        'casc_extract.py',
        '-m', 'batch',
        '--cdn',
        '-o', str(paths.cdn)
    ]
    if realm != WowRealm.LIVE:
        cmd.append(f'--{realm}')
    
    print(f'Extracting CDN data to {paths.cdn}...')
    subprocess.run(cmd, cwd=casc_dir, check=True)

def process_dbc_data(paths: Paths, version: str, realm: WowRealm, tasks: TaskConfig, update_simc: bool):
    """Process DBC data using dbc_extract."""
    dbc_dir = paths.simc / 'dbc_extract3'
    game_tables = paths.cdn / version / 'GameTables'
    client_data = paths.cdn / version / 'DBFilesClient'
    
    # Base commands
    gt_cmd = [
        PYTHON_PATH, 'dbc_extract.py',
        '-p', str(game_tables),
        '-b', version
    ]
    dbc_cmd = [
        PYTHON_PATH, 'dbc_extract.py',
        '-p', str(client_data),
        '-b', version
    ]
    
    # Add hotfix if available
    if paths.wow:
        realm_path = '_retail_'
        if realm == WowRealm.PTR:
            realm_path = '_ptr_'
        elif realm == WowRealm.BETA:
            realm_path = '_beta_'
        
        hotfix = paths.wow / realm_path / 'Cache' / 'ADB' / 'enUS' / 'DBCCache.bin'
        if hotfix.is_file():
            print(f'Using hotfix file: {hotfix}')
            dbc_cmd.extend(['--hotfix', str(hotfix)])
    
    # Update simc data if requested
    if update_simc:
        print('Updating simc data...')
        simcGtExtractCmd = [*gt_cmd, '-t', 'scale', '-o']
        simcDbcExtractCmd = [*dbc_cmd, '-t', 'output']
        
        if realm == WowRealm.PTR:
            simcGtExtractCmd.extend([
                str(paths.simc / 'engine' / 'dbc' / 'generated' / 'sc_scale_data_ptr.inc'),
                '--prefix=ptr'
            ])
            simcDbcExtractCmd.extend([
                str(paths.simc / 'dbc_extract3' / 'ptr.conf'),
                '--prefix=ptr'
            ])
        else:
            simcGtExtractCmd.append(str(paths.simc / 'engine' / 'dbc' / 'generated' / 'sc_scale_data.inc'))
            simcDbcExtractCmd.append(str(paths.simc / 'dbc_extract3' / 'live.conf'))
        
        subprocess.run(simcGtExtractCmd, cwd=dbc_dir, check=True)
        subprocess.run(simcDbcExtractCmd, cwd=dbc_dir, check=True)
    
    # Process each dbfile
    output_dir = paths.scripts / 'DBC' / 'generated'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print('Converting DBC files to CSV...')
    for dbfile in tasks.dbfiles:
        print(f'  Processing {dbfile}...')
        output = output_dir / f'{dbfile}.csv'
        full_cmd = [*dbc_cmd, '-t', 'csv', dbfile]
        with output.open('w') as f:
            subprocess.run(full_cmd, cwd=dbc_dir, stdout=f, check=True)

def run_parsers(paths: Paths, tasks: TaskConfig):
    """Run all data parsers."""
    parsers_dir = paths.scripts / 'parsers'
    print('Running parsers...')
    for parser in tasks.parsers:
        print(f'  Running {parser}...')
        subprocess.run(
            [PYTHON_PATH, f'{parser}.py'],
            cwd=parsers_dir,
            check=True
        )

def update_lua_meta(paths: Paths, start_time: int, version: str):
    """Update Lua metadata."""
    meta_path = paths.scripts / 'tools' / 'luaMeta.py'
    print('Updating Lua metadata...')
    subprocess.run(
        [
            PYTHON_PATH,
            meta_path,
            f'--mtime={start_time}',
            f'--version={version}'
        ],
        check=True
    )

def main():
    """Main execution function."""
    # Setup
    args = setup_argument_parser().parse_args()
    start_time = int(datetime.datetime.now().timestamp())
    
    # Initialize paths
    root_dir = Path(__file__).parent.parent  # hero-dbc root
    paths = Paths(
        root=root_dir,
        scripts=root_dir / 'scripts',
        cdn=root_dir / 'scripts' / 'CDN',
        dbc=root_dir / 'scripts' / 'DBC',
        simc=SIMC_DIR,
        wow=Path(args.wow_dir) if args.wow_dir else find_wow_directory(root_dir / 'scripts')
    )
    
    # Create necessary directories
    paths.cdn.mkdir(parents=True, exist_ok=True)
    paths.dbc.mkdir(parents=True, exist_ok=True)
    
    # Load task configuration
    with open(paths.scripts / 'tasks.json') as f:
        tasks = TaskConfig.model_validate_json(f.read())
    
    try:
        # Extract and process data
        extract_cdn_data(paths, args.wow_realm)
        version = get_wow_version(paths.scripts, paths.cdn)
        print(f'Using WoW version: {version}')
        
        process_dbc_data(paths, version, args.wow_realm, tasks, args.update_simc)
        run_parsers(paths, tasks)
        update_lua_meta(paths, start_time, version)
        
        print('Data extraction completed successfully.')
        
    except subprocess.CalledProcessError as e:
        print(f'Error during extraction: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise

if __name__ == '__main__':
    main()
