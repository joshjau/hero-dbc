# -*- coding: utf-8 -*-
"""
Optimized Spell Melee Range Parser
Processes SpellRange.csv and SpellMisc.csv to generate Lua table of spell ranges
Author: Quentin Giraud <dev@aethys.io>
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
import mmap
import re
from rich.console import Console
from tqdm import tqdm
from collections import defaultdict

# Initialize rich console for better output formatting
console = Console()

# Compile regex patterns once for better performance
CSV_PATTERN = re.compile(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)')

# Define constants for better maintainability and performance
MELEE_FLAG = 1
MAX_RANGE_THRESHOLD = 100
CHUNK_SIZE = 500
NEEDED_RANGE_COLUMNS = {'id', 'min_range_1', 'max_range_1', 'flag'}
NEEDED_MISC_COLUMNS = {'id_parent', 'id_range'}

def mmap_read_csv(file_path: Path, needed_columns: Set[str]) -> List[Dict]:
    """
    Memory-mapped CSV reading for large files with regex splitting
    Only loads specified columns for better memory efficiency
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Process header and get indices of needed columns
                header = CSV_PATTERN.split(mm.readline().decode('utf-8').strip())
                col_indices = {col: idx for idx, col in enumerate(header) if col in needed_columns}
                
                if not all(col in col_indices for col in needed_columns):
                    missing = needed_columns - set(col_indices.keys())
                    raise ValueError(f"Missing required columns: {missing}")
                
                rows = []
                while True:
                    line = mm.readline()
                    if not line:
                        break
                    
                    values = CSV_PATTERN.split(line.decode('utf-8').strip())
                    if len(values) >= len(header):
                        # Only extract needed columns
                        rows.append({col: values[idx] for col, idx in col_indices.items()})
                
                return rows
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_spell_range_data(range_data: List[Dict]) -> Dict[str, Tuple[str, str, int]]:
    """
    Process SpellRange.csv data with optimized filtering
    Returns: Dict[range_id, (min_range, max_range, flag)]
    """
    ranges = {}
    
    for row in tqdm(range_data, desc="Processing spell ranges"):
        try:
            min_range = float(row['min_range_1'])
            max_range = float(row['max_range_1'])
            flag = int(row['flag'])
            
            # Filter valid ranges (max range > 0 and <= MAX_RANGE_THRESHOLD)
            if 0 < max_range <= MAX_RANGE_THRESHOLD:
                ranges[row['id']] = (
                    str(int(min_range)),
                    str(int(max_range)),
                    flag
                )
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Skipping invalid range data: {e}[/yellow]")
            continue
    
    return ranges

def process_spell_misc_data(misc_data: List[Dict], valid_ranges: Dict) -> List[Dict]:
    """
    Process SpellMisc.csv data with optimized grouping
    Uses early filtering for better performance
    """
    spell_groups = defaultdict(list)
    valid_range_ids = set(valid_ranges.keys())  # Convert to set for O(1) lookup
    
    # Group by parent_id for efficient processing
    for row in misc_data:
        if row['id_range'] in valid_range_ids:  # O(1) lookup
            try:
                parent_id = int(row['id_parent'])
                spell_groups[parent_id].append(row)
            except ValueError:
                continue
    
    # Take first valid entry for each spell and sort
    return sorted(
        (rows[0] for rows in spell_groups.values() if rows),
        key=lambda x: int(x['id_parent'])
    )

def write_lua_file(output_file: Path, valid_rows: List[Dict], ranges: Dict) -> None:
    """
    Optimized Lua file writing with chunked output and string buffer
    """
    try:
        header = [
            "-- Auto-generated spell melee range data",
            "-- Format: [SpellID] = { IsMelee, MinRange, MaxRange }",
            "local SpellMeleeRange = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellMeleeRange = setmetatable({{}}, {{__index = function() return {{false, 0, 0}} end}})",
            ""
        ]
        
        # Pre-calculate chunk size based on data size
        chunk_size = min(CHUNK_SIZE, max(100, len(valid_rows) // 10))
        
        # Process entries in chunks with string buffer
        chunks = []
        current_chunk = []
        for i, row in enumerate(valid_rows):
            range_data = ranges[row['id_range']]
            is_melee = 'true' if range_data[2] == MELEE_FLAG else 'false'
            
            current_chunk.append(
                f"SpellMeleeRange[{row['id_parent']}] = {{ {is_melee}, {range_data[0]}, {range_data[1]} }}"
            )
            
            if i % chunk_size == chunk_size - 1:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(SpellMeleeRange, nil)",
            "",
            "HeroDBC.DBC.SpellMeleeRange = SpellMeleeRange",
            "return SpellMeleeRange"
        ]
        
        # Single write operation with minimal string operations
        with output_file.open('w', encoding='utf-8') as file:
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

    console.print("[cyan]Loading SpellRange.csv...[/cyan]")
    range_data = mmap_read_csv(generated_dir / 'SpellRange.csv', NEEDED_RANGE_COLUMNS)
    ranges = process_spell_range_data(range_data)

    console.print("[cyan]Loading SpellMisc.csv...[/cyan]")
    misc_data = mmap_read_csv(generated_dir / 'SpellMisc.csv', NEEDED_MISC_COLUMNS)
    valid_rows = process_spell_misc_data(misc_data, ranges)
    
    output_file = addon_enum_dir / 'SpellMeleeRange.lua'
    write_lua_file(output_file, valid_rows, ranges)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
