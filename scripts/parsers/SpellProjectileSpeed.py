# -*- coding: utf-8 -*-
"""
Optimized Spell Projectile Speed Parser
Processes SpellMisc.csv to generate Lua table of projectile speeds
Author: Quentin Giraud <dev@aethys.io>
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, NamedTuple
import mmap
import re
from rich.console import Console
from tqdm import tqdm
from collections import defaultdict
from statistics import mean
import multiprocessing as mp
from functools import partial

# Initialize rich console for better output formatting
console = Console()

# Compile regex patterns once for better performance
CSV_PATTERN = re.compile(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)')

# Define constants for better maintainability and performance
MIN_PROJECTILE_SPEED = 0
CHUNK_SIZE = 500
NEEDED_MISC_COLUMNS = {'id_parent', 'proj_speed'}
CPU_COUNT = mp.cpu_count()
BUFFER_SIZE = 8192  # Optimal buffer size for mmap operations

# Add this class for better data structure
class ProjectileData(NamedTuple):
    id_parent: int
    proj_speed: int

def mmap_read_csv(file_path: Path, needed_columns: Set[str]) -> List[Dict]:
    """
    Memory-mapped CSV reading with optimized buffer size
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Simplified mmap call with correct number of arguments
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Process header and get indices of needed columns
                header = CSV_PATTERN.split(mm.readline().decode('utf-8').strip())
                col_indices = {col: idx for idx, col in enumerate(header) if col in needed_columns}
                
                if not all(col in col_indices for col in needed_columns):
                    missing = needed_columns - set(col_indices.keys())
                    raise ValueError(f"Missing required columns: {missing}")
                
                # Use buffered reading for better performance
                rows = []
                buffer = []
                buffer_size = BUFFER_SIZE
                
                while True:
                    line = mm.readline()
                    if not line:
                        break
                    
                    values = CSV_PATTERN.split(line.decode('utf-8').strip())
                    if len(values) >= len(header):
                        # Only extract needed columns
                        rows.append({col: values[idx] for col, idx in col_indices.items()})
                    
                    # Process in chunks for memory efficiency
                    if len(buffer) >= buffer_size:
                        rows.extend(buffer)
                        buffer = []
                
                if buffer:
                    rows.extend(buffer)
                
                return rows
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_chunk(chunk: List[Dict]) -> tuple[List[ProjectileData], List[int]]:
    """
    Process a chunk of spell data in parallel
    """
    spell_data = []
    speeds = []
    
    for row in chunk:
        try:
            proj_speed = float(row['proj_speed'])
            if proj_speed > MIN_PROJECTILE_SPEED:
                parent_id = int(row['id_parent'])
                speed_int = int(proj_speed)
                spell_data.append(ProjectileData(parent_id, speed_int))
                speeds.append(speed_int)
        except (ValueError, KeyError):
            continue
            
    return spell_data, speeds

def process_spell_misc_data(misc_data: List[Dict]) -> tuple[List[Dict], float]:
    """
    Process SpellMisc.csv data with parallel processing
    """
    # Split data into chunks for parallel processing
    chunk_size = max(100, len(misc_data) // (CPU_COUNT * 2))
    chunks = [misc_data[i:i + chunk_size] for i in range(0, len(misc_data), chunk_size)]
    
    # Process chunks in parallel
    with mp.Pool(CPU_COUNT) as pool:
        results = list(tqdm(
            pool.imap(process_chunk, chunks),
            total=len(chunks),
            desc="Processing projectile speeds"
        ))
    
    # Combine results
    all_spell_data = []
    all_speeds = []
    for spell_data, speeds in results:
        all_spell_data.extend(spell_data)
        all_speeds.extend(speeds)
    
    # Sort and convert to final format
    valid_rows = sorted(
        [{'id_parent': data.id_parent, 'proj_speed': data.proj_speed} 
         for data in all_spell_data],
        key=lambda x: x['id_parent']
    )
    
    # Calculate mean speed
    mean_speed = mean(all_speeds) if all_speeds else 0
    
    return valid_rows, mean_speed

def write_lua_file(output_file: Path, valid_rows: List[Dict]) -> None:
    """
    Optimized Lua file writing with improved string handling
    """
    try:
        header = [
            "-- Auto-generated spell projectile speed data",
            "-- Format: [SpellID] = ProjectileSpeed",
            "local SpellProjectileSpeed = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellProjectileSpeed = setmetatable({{}}, {{__index = function() return 0 end}})",
            "-- Estimated projectile speeds count: {len(valid_rows)}",
            ""
        ]
        
        # Use string.format for better performance
        entry_template = "SpellProjectileSpeed[{0}] = {1}"
        
        # Process entries in optimized chunks
        chunk_size = min(CHUNK_SIZE, max(100, len(valid_rows) // 10))
        chunks = []
        current_chunk = []
        
        for i, row in enumerate(valid_rows):
            current_chunk.append(entry_template.format(
                row['id_parent'],
                row['proj_speed']
            ))
            
            if i % chunk_size == chunk_size - 1:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(SpellProjectileSpeed, nil)",
            "",
            "HeroDBC.DBC.SpellProjectileSpeed = SpellProjectileSpeed",
            "return SpellProjectileSpeed"
        ]
        
        # Write with larger buffer size
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            file.write('\n'.join(chunks))
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(valid_rows)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellMisc.csv...[/cyan]")
    misc_data = mmap_read_csv(generated_dir / 'SpellMisc.csv', NEEDED_MISC_COLUMNS)
    valid_rows, mean_speed = process_spell_misc_data(misc_data)
    
    if mean_speed > 0:
        console.print(f"[green]Projectile Speed Mean: {mean_speed:.2f}[/green]")
    else:
        console.print("[yellow]No valid projectile speeds found in the data[/yellow]")
    
    output_file = addon_enum_dir / 'SpellProjectileSpeed.lua'
    write_lua_file(output_file, valid_rows)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
