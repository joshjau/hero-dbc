# -*- coding: utf-8 -*-
"""
Optimized Item Data Parser
Processes ItemSparse and JournalEncounterItem to generate JSON item database
Author: Kutikuti
"""

import sys
import gc
from pathlib import Path
from typing import Dict, List, Set, NamedTuple, Generator, Union
import mmap
import re
import json
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

# Item constants
VALID_ITEM_LEVELS = {158, 200, 226, 233}  # dungeon, castle nathria, sanctum of domination
NO_MATERIAL_TYPES = {'trinket', 'neck', 'finger', 'back'}

# Column definitions
ITEM_SPARSE_COLUMNS = {
    'id', 'name', 'ilevel', 'quality', 'inv_type', 'material',
    'stat_type_1', 'stat_type_2', 'stat_type_3', 'stat_type_4', 'stat_type_5',
    'socket_color_1', 'socket_color_2', 'socket_color_3'
}
JOURNAL_ENCOUNTER_COLUMNS = {'id_item', 'id_encounter'}

# Mapping dictionaries
ITEM_TYPE_MAP = {
    1: 'head',
    2: 'neck',
    3: 'shoulders',
    5: 'chest',
    6: 'waist',
    7: 'legs',
    8: 'feet',
    9: 'wrists',
    10: 'hands',
    11: 'finger',
    12: 'trinket',
    13: 'weapon',
    14: 'shield',
    15: 'ranged',
    16: 'back',
    17: '2hweapon',
    20: 'chest'
}

ITEM_MATERIAL_MAP = {
    6: 'plate',
    5: 'mail',
    8: 'leather',
    7: 'cloth'
}

STAT_TYPE_MAP = {
    3: 'agi',
    4: 'str',
    5: 'int',
    7: 'stam',
    32: 'crit',
    36: 'haste',
    40: 'vers',
    49: 'mastery',
    50: 'bonus_armor',
    62: 'leech',
    63: 'avoidance',
    71: 'agi/str/int',
    72: 'agi/str',
    73: 'agi/int',
    74: 'str/int',
}

class ItemData(NamedTuple):
    """Structured item data for better type safety"""
    id: int
    name: str
    ilevel: int
    type: str
    material: str
    stats: List[str]
    gems: int
    source: str

def mmap_read_csv(file_path: Path, needed_columns: Set[str]) -> List[Dict]:
    """Memory-mapped CSV reading with optimized buffer size and multiple encoding support"""
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # First try reading normally to validate encoding
                header = CSV_PATTERN.split(f.readline().strip())
                col_indices = {col: idx for idx, col in enumerate(header) if col in needed_columns}
                
                if not all(col in col_indices for col in needed_columns):
                    missing = needed_columns - set(col_indices.keys())
                    raise ValueError(f"Missing required columns: {missing}")
                
                # Read data rows (skip header since we already read it)
                rows = []
                for line_num, line in enumerate(f, 2):  # Start at 2 since we read header
                    try:
                        values = CSV_PATTERN.split(line.strip())
                        if len(values) >= len(header):
                            row_data = {}
                            for col, idx in col_indices.items():
                                try:
                                    row_data[col] = values[idx].strip('"').strip()
                                except IndexError:
                                    console.print(f"[yellow]Warning: Missing value for column {col} on line {line_num}[/yellow]")
                                    continue
                            if row_data:
                                rows.append(row_data)
                    except Exception as e:
                        console.print(f"[yellow]Warning: Skipping malformed line {line_num}: {str(e)}[/yellow]")
                        continue
                
                console.print(f"[green]Successfully read {file_path} using {encoding} encoding[/green]")
                return rows
                    
        except UnicodeDecodeError:
            continue  # Try next encoding
        except Exception as e:
            console.print(f"[yellow]Failed to read with {encoding}: {str(e)}[/yellow]")
            continue
            
    raise UnicodeDecodeError(f"Failed to decode {file_path} with any known encoding")

def get_item_stats(row: Dict) -> List[str]:
    """Process item stats with improved error handling"""
    stats = []
    for i in range(1, 6):
        try:
            stat_type = int(row[f'stat_type_{i}'])
            if stat := STAT_TYPE_MAP.get(stat_type):
                stats.append(stat)
        except (ValueError, KeyError):
            continue
    return stats

def compute_gem_number(row: Dict) -> int:
    """Calculate number of gem sockets"""
    try:
        return sum(1 for i in range(1, 4) 
                  if int(row[f'socket_color_{i}']) != 0)
    except (ValueError, KeyError):
        return 0

def compute_source(item_id: int, quality: int, item_type: str, ilevel: int, encounter_table: Dict[int, int]) -> str:
    """Determine item source with improved logic"""
    if ilevel == 158:
        return "dungeon" if item_id in encounter_table else "pvp"
    elif ilevel == 200:
        return "castle_nathria" if item_id in encounter_table else "other"
    elif ilevel in {226, 233}:
        return "sanctum_of_domination"
    return ""

def process_item_data(row: Dict, encounter_table: Dict[int, int]) -> Union[ItemData, None]:
    """Process single item data with validation"""
    try:
        item_id = int(row['id'])
        ilevel = int(row['ilevel'])
        
        if ilevel not in VALID_ITEM_LEVELS:
            return None
            
        inv_type = int(row['inv_type'])
        item_type = ITEM_TYPE_MAP.get(inv_type, '')
        if not item_type:
            return None
            
        return ItemData(
            id=item_id,
            name=row['name'],
            ilevel=ilevel,
            type=item_type,
            material=ITEM_MATERIAL_MAP.get(int(row['material']), ''),
            stats=get_item_stats(row),
            gems=compute_gem_number(row),
            source=compute_source(
                item_id, 
                int(row['quality']), 
                item_type, 
                ilevel, 
                encounter_table
            )
        )
    except (ValueError, KeyError) as e:
        console.print(f"[yellow]Warning: Invalid item data: {row} - {str(e)}[/yellow]")
        return None

def organize_items(items: List[ItemData]) -> Dict:
    """Organize items into final structure"""
    # Initialize with proper nested structure
    organized = {}
    
    for item in tqdm(items, desc="Organizing items"):
        try:
            if item.type in NO_MATERIAL_TYPES:
                # Initialize list for types without materials if needed
                if item.type not in organized:
                    organized[item.type] = []
                organized[item.type].append(item._asdict())
            else:
                # Initialize nested dict for types with materials if needed
                if item.type not in organized:
                    organized[item.type] = {}
                if item.material not in organized[item.type]:
                    organized[item.type][item.material] = []
                organized[item.type][item.material].append(item._asdict())
        except Exception as e:
            console.print(f"[yellow]Warning: Error organizing item {item.id} ({item.name}): {str(e)}[/yellow]")
            continue
    
    return organized

def write_json_file(output_file: Path, data: Dict) -> None:
    """Write JSON output with optimized formatting"""
    try:
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as f:
            json.dump(data, f, indent=4, sort_keys=True)
        console.print(f"[green]Successfully wrote item data to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    parsed_dir = base_dir / 'scripts' / 'DBC' / 'parsed'

    # Load encounter data
    console.print("[cyan]Loading encounter data...[/cyan]")
    encounter_data = mmap_read_csv(generated_dir / 'JournalEncounterItem.csv', JOURNAL_ENCOUNTER_COLUMNS)
    encounter_table = {int(row['id_item']): int(row['id_encounter']) 
                      for row in encounter_data}

    # Process items
    console.print("[cyan]Loading item data...[/cyan]")
    item_data = mmap_read_csv(generated_dir / 'ItemSparse.csv', ITEM_SPARSE_COLUMNS)
    
    processed_items = []
    for row in tqdm(item_data, desc="Processing items"):
        if item := process_item_data(row, encounter_table):
            processed_items.append(item)
    
    # Organize and write data
    organized_data = organize_items(processed_items)
    output_file = parsed_dir / 'ItemData.json'
    write_json_file(output_file, organized_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
