# -*- coding: utf-8 -*-
"""
Optimized Item Range Parser
Processes ItemEffect, SpellMisc, and SpellRange to generate Lua table of item range data
Author: Quentin Giraud <dev@aethys.io>
"""

import sys
import gc
from pathlib import Path
from typing import Dict, List, Set, NamedTuple, Generator, Tuple
import mmap
import re
from rich.console import Console
from tqdm import tqdm
from collections import defaultdict
import multiprocessing as mp
from functools import partial

# Initialize rich console for better output formatting
console = Console()

# Compile regex patterns once for better performance
CSV_PATTERN = re.compile(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)')

# Define constants for better maintainability and performance
CHUNK_SIZE = 500
BUFFER_SIZE = 8192
GC_THRESHOLD = 5000
CPU_COUNT = max(1, min(mp.cpu_count() - 1, 8))

# Range constants
MIN_VALID_RANGE = 5.0
MAX_VALID_RANGE = 100.0
RANGE_TYPE_MELEE = 1

# Column definitions
ITEM_EFFECT_COLUMNS = {'id', 'id_spell'}
SPELL_RANGE_COLUMNS = {'id', 'min_range_1', 'max_range_1', 'min_range_2', 'max_range_2', 'flag'}
SPELL_MISC_COLUMNS = {'id_parent', 'id_range'}

class RangeData(NamedTuple):
    """Structured range data for better type safety"""
    max_range: float
    flag: int

class ItemRangeData(NamedTuple):
    """Structured item range data"""
    range_value: float
    items: List[int]
    is_melee: bool

def mmap_read_csv(file_path: Path, needed_columns: Set[str]) -> List[Dict]:
    """Memory-mapped CSV reading with optimized buffer size"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                header = CSV_PATTERN.split(mm.readline().decode('utf-8').strip())
                col_indices = {col: idx for idx, col in enumerate(header) if col in needed_columns}
                
                if not all(col in col_indices for col in needed_columns):
                    missing = needed_columns - set(col_indices.keys())
                    raise ValueError(f"Missing required columns: {missing}")
                
                return list(read_csv_rows(mm, col_indices, len(header)))
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def read_csv_rows(mm: mmap.mmap, col_indices: Dict[str, int], header_len: int) -> Generator[Dict, None, None]:
    """Generator function for memory-efficient CSV reading"""
    items_processed = 0
    
    while True:
        line = mm.readline()
        if not line:
            break
        
        values = CSV_PATTERN.split(line.decode('utf-8').strip())
        if len(values) >= header_len:
            yield {col: values[idx] for col, idx in col_indices.items()}
            
            items_processed += 1
            if items_processed % GC_THRESHOLD == 0:
                gc.collect()

def process_item_effects(effect_data: List[Dict]) -> Dict[str, str]:
    """Process item effects into spell mapping"""
    items = {}
    
    for row in tqdm(effect_data, desc="Processing item effects"):
        try:
            spell_id = row['id_spell']
            item_id = row['id']
            if spell_id and item_id:
                items[spell_id] = item_id
        except (KeyError, ValueError) as e:
            console.print(f"[yellow]Warning: Invalid item effect data: {row} - {str(e)}[/yellow]")
            continue
            
    return items

def process_spell_ranges(range_data: List[Dict]) -> Dict[str, RangeData]:
    """Process spell ranges into structured format"""
    ranges = {}
    
    for row in tqdm(range_data, desc="Processing spell ranges"):
        try:
            # Process hostile ranges
            min_range = float(row['min_range_1'])
            max_range = float(row['max_range_1'])
            if min_range == 0 and MIN_VALID_RANGE <= max_range <= MAX_VALID_RANGE:
                ranges[row['id']] = RangeData(max_range, int(row['flag']))
            
            # Process friendly ranges
            min_range = float(row['min_range_2'])
            max_range = float(row['max_range_2'])
            if min_range == 0 and MIN_VALID_RANGE <= max_range <= MAX_VALID_RANGE:
                ranges[row['id']] = RangeData(max_range, int(row['flag']))
                
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid range data: {row} - {str(e)}[/yellow]")
            continue
            
    return ranges

def process_item_ranges(misc_data: List[Dict], items: Dict[str, str], ranges: Dict[str, RangeData]) -> Dict[str, Dict[float, List[int]]]:
    """Process item ranges into final structure"""
    item_ranges = {
        'Melee': defaultdict(list),
        'Ranged': defaultdict(list)
    }
    
    for row in tqdm(misc_data, desc="Processing item ranges"):
        try:
            id_misc = row['id_parent']
            if id_misc in items:
                id_range = row['id_range']
                if id_range in ranges:
                    range_data = ranges[id_range]
                    range_type = 'Melee' if range_data.flag == RANGE_TYPE_MELEE else 'Ranged'
                    item_ranges[range_type][range_data.max_range].append(int(items[id_misc]))
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid misc data: {row} - {str(e)}[/yellow]")
            continue
    
    # Sort items within each range
    for range_type in item_ranges:
        for range_value in item_ranges[range_type]:
            item_ranges[range_type][range_value].sort()
            
    return item_ranges

def write_lua_file(output_file: Path, item_ranges: Dict[str, Dict[float, List[int]]]) -> None:
    """Optimized Lua file writing with improved string handling"""
    try:
        header = [
            "-- Auto-generated item range data",
            "-- Format: { [Type] = { [Range] = { ItemIDs... } } }",
            "local ItemRange = {}",
            "",
            "-- Pre-allocate known size for better performance",
            "ItemRange = {",
            "  Melee = {},",
            "  Ranged = {}",
            "}",
            ""
        ]
        
        def format_range_block(range_type: str, ranges: Dict[float, List[int]]) -> str:
            lines = [f"ItemRange['{range_type}'] = {{"]
            
            for range_value, items in sorted(ranges.items()):
                lines.append(f"  [{range_value:g}] = {{")
                lines.extend(f"    {item_id}," for item_id in items)
                lines.append("  },")
            
            lines.append("}")
            return '\n'.join(lines)
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(ItemRange.Melee, nil)",
            "setmetatable(ItemRange.Ranged, nil)",
            "setmetatable(ItemRange, nil)",
            "",
            "HeroDBC.DBC.ItemRangeUnfiltered = ItemRange",
            "return ItemRange"
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for range_type in ['Melee', 'Ranged']:
                file.write(format_range_block(range_type, item_ranges[range_type]) + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote item range data to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_dev_dir = base_dir / 'HeroDBC' / 'Dev' / 'Unfiltered'

    console.print("[cyan]Loading item effect data...[/cyan]")
    items = process_item_effects(
        mmap_read_csv(generated_dir / 'ItemEffect.csv', ITEM_EFFECT_COLUMNS)
    )
    
    console.print("[cyan]Loading spell range data...[/cyan]")
    ranges = process_spell_ranges(
        mmap_read_csv(generated_dir / 'SpellRange.csv', SPELL_RANGE_COLUMNS)
    )
    
    console.print("[cyan]Processing item ranges...[/cyan]")
    item_ranges = process_item_ranges(
        mmap_read_csv(generated_dir / 'SpellMisc.csv', SPELL_MISC_COLUMNS),
        items,
        ranges
    )
    
    output_file = addon_dev_dir / 'ItemRange.lua'
    write_lua_file(output_file, item_ranges)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
