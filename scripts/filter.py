#!/usr/bin/env python3
"""
Optimized Filter Script
Processes and filters DBC data for HeroLib/HeroCache
"""

import sys
import datetime
import json
import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import logging
from rich.console import Console
from rich.progress import Progress
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# Initialize rich console for better output formatting
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_PACKAGES = [
    'pandas',
    'numpy',
    'SLPP-23',
    'tqdm',
    'requests',
    'rich'
]

class FilterProcessor:
    """Handles DBC data filtering and processing"""
    
    def __init__(self):
        self.filter_start_time = math.floor(datetime.datetime.now().timestamp())
        self.base_dir = Path(__file__).parent.parent
        self.scripts_dir = self.base_dir / 'scripts'
        self.cdn_dir = self.scripts_dir / 'CDN'
        self.simc_dir = self.base_dir.parent / 'simulationcraft' / 'simc'
        
        # Ensure all directories exist
        self.cdn_dir.mkdir(parents=True, exist_ok=True)
        
    def ensure_dependencies(self) -> None:
        """Ensure all required packages are installed"""
        try:
            for package in REQUIRED_PACKAGES:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    console.print(f"[yellow]Installing {package}...[/yellow]")
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package
                    ])
        except Exception as e:
            console.print(f"[red]Failed to install dependencies: {str(e)}[/red]")
            sys.exit(1)
            
    def detect_wow_version(self) -> str:
        """Detect current WoW version"""
        try:
            version_script = self.scripts_dir / 'tools' / 'wowVersion.py'
            result = subprocess.run(
                [sys.executable, str(version_script), f'--cdnDirPath={self.cdn_dir}'],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            console.print(f"[green]Detected WoW version: {version}[/green]")
            return version
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to detect WoW version: {str(e)}[/red]")
            sys.exit(1)
            
    def load_tasks(self) -> Dict[str, Any]:
        """Load tasks configuration"""
        try:
            tasks_file = self.scripts_dir / 'tasks.json'
            with tasks_file.open('r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]Failed to load tasks: {str(e)}[/red]")
            sys.exit(1)
            
    def process_filter(self, filter_name: str) -> None:
        """Process a single filter"""
        try:
            filter_script = self.scripts_dir / 'filters' / f'{filter_name}.py'
            result = subprocess.run(
                [sys.executable, str(filter_script)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                console.print(f"[yellow]Warning: Filter {filter_name} failed: {result.stderr}[/yellow]")
            else:
                console.print(f"[green]Successfully processed {filter_name}[/green]")
                
        except Exception as e:
            console.print(f"[red]Error processing filter {filter_name}: {str(e)}[/red]")
            
    def update_lua_metadata(self, version: str) -> None:
        """Update Lua metadata"""
        try:
            meta_script = self.scripts_dir / 'tools' / 'luaMeta.py'
            subprocess.run(
                [
                    sys.executable,
                    str(meta_script),
                    f'--mtime={self.filter_start_time}',
                    f'--version={version}'
                ],
                check=True
            )
            console.print("[green]Successfully updated Lua metadata[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to update Lua metadata: {str(e)}[/red]")
            
    def run(self) -> None:
        """Main processing pipeline"""
        try:
            # Ensure dependencies
            self.ensure_dependencies()
            
            # Import required packages after ensuring they're installed
            import pandas as pd
            import numpy as np
            from slpp import slpp as lua
            from tqdm import tqdm
            import requests
            
            # Detect version
            version = self.detect_wow_version()
            
            # Load tasks
            tasks = self.load_tasks()
            
            # Process filters
            console.print("[cyan]Processing filters...[/cyan]")
            with Progress() as progress:
                task = progress.add_task("Processing", total=len(tasks['filters']))
                
                # Process filters in parallel
                with ThreadPoolExecutor(max_workers=4) as executor:
                    for filter_name in tasks['filters']:
                        executor.submit(self.process_filter, filter_name)
                        progress.update(task, advance=1)
            
            # Update metadata
            self.update_lua_metadata(version)
            
            console.print("[green]Filter processing completed successfully[/green]")
            
        except Exception as e:
            console.print(f"[red]Filter processing failed: {str(e)}[/red]")
            sys.exit(1)

def main():
    processor = FilterProcessor()
    processor.run()

if __name__ == '__main__':
    main()
