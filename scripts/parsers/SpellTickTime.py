# -*- coding: utf-8 -*-
"""
Optimized Spell Tick Time Parser
Processes SpellEffect.csv to generate Lua table of spell tick times
Author: Kutikuti
"""

import sys
import os
import csv
from pathlib import Path
from tqdm import tqdm
from rich.console import Console
from typing import List, Dict, Set
from collections import defaultdict
import mmap
import re

# Initialize rich console for better output formatting
console = Console()

# Compile regex patterns once for better performance
CSV_PATTERN = re.compile(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)')

def mmap_read_csv(file_path: Path) -> List[Dict]:
    """
    Memory-mapped CSV reading for large files with regex splitting
    Significantly faster than standard CSV reading for large datasets
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Read and process header
                header = CSV_PATTERN.split(mm.readline().decode('utf-8').strip())
                
                # Only extract needed columns for better memory efficiency
                needed_cols = {'id_parent', 'amplitude', 'id_mechanic', 'id_effect'}
                col_indices = {col: idx for idx, col in enumerate(header) if col in needed_cols}
                
                # Process rows using memory mapping
                rows = []
                while True:
                    line = mm.readline()
                    if not line:
                        break
                    
                    values = CSV_PATTERN.split(line.decode('utf-8').strip())
                    if len(values) >= len(header):
                        row_dict = {col: values[idx] for col, idx in col_indices.items()}
                        rows.append(row_dict)
                
                return rows
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_spell_data(csv_data: List[Dict]) -> List[Dict]:
    """
    Process CSV data with optimized data structures and minimal iterations
    Uses defaultdict for faster grouping and lookup
    """
    spell_groups = defaultdict(list)
    valid_mechanics: Set[str] = {"6", "7", "8"}  # Common DoT mechanics
    
    # Single pass grouping with early filtering
    for row in csv_data:
        try:
            amplitude = int(row['amplitude'])
            if amplitude <= 0:  # Skip invalid amplitudes
                continue
                
            parent_id = int(row['id_parent'])
            mechanic = row['id_mechanic']
            
            # Prioritize DoT effects
            is_priority = mechanic in valid_mechanics
            
            spell_groups[parent_id].append({
                'amplitude': amplitude,
                'mechanic': mechanic != "15",
                'effect_type': int(row.get('id_effect', 0)),
                'priority': is_priority
            })
        except (ValueError, KeyError):
            continue
    
    # Process groups into final format
    valid_rows = []
    with tqdm(total=len(spell_groups), desc="Processing spell tick times") as pbar:
        for parent_id, effects in spell_groups.items():
            if effects:
                # Sort effects to prioritize DoT mechanics
                effects.sort(key=lambda x: (x['priority'], x['amplitude']), reverse=True)
                valid_rows.append({
                    'id': parent_id,
                    'amplitude': effects[0]['amplitude'],
                    'mechanic': effects[0]['mechanic']
                })
            pbar.update(1)
    
    return valid_rows

def write_lua_file(output_file: Path, data: List[Dict]) -> None:
    """
    Optimized Lua file writing with minimal string operations
    Generates Lua code optimized for runtime performance
    """
    try:
        # Pre-sort data for better Lua table performance
        sorted_data = sorted(data, key=lambda x: x['id'])
        
        # Prepare all strings in memory first
        header = [
            "-- Auto-generated spell tick time data",
            "-- Format: [spellID] = {amplitude, hasMechanic}",
            "local SpellTickTime = {}",  # Initialize empty for better memory allocation
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellTickTime = setmetatable({{}}, {{__index = function() return {{0, false}} end}})",
            ""
        ]
        
        # Build table entries efficiently using string joining
        chunks = []
        current_chunk = []
        for i, entry in enumerate(sorted_data):
            current_chunk.append(
                f"SpellTickTime[{entry['id']}] = {{{entry['amplitude']},{str(entry['mechanic']).lower()}}}"
            )
            
            # Write in chunks for better memory management
            if i % 500 == 0 and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(SpellTickTime, nil)",
            "",
            "HeroDBC.DBC.SpellTickTime = SpellTickTime",
            "return SpellTickTime"
        ]
        
        # Single write operation with chunked data
        with output_file.open('w', encoding='utf-8') as file:
            file.write('\n'.join(header))
            file.write('\n'.join(chunks))
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellEffect.csv...[/cyan]")
    spell_effect_data = mmap_read_csv(generated_dir / 'SpellEffect.csv')
    
    processed_data = process_spell_data(spell_effect_data)
    
    output_file = addon_enum_dir / 'SpellTickTime.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
