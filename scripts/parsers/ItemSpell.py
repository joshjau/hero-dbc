# -*- coding: utf-8 -*-
"""
Optimized Item Spell Parser
Processes ItemEffect and ItemXItemEffect to generate Lua table of item spell mappings
Author: Kutikuti
"""

import sys
import gc
from pathlib import Path
from typing import Dict, List, Set, NamedTuple, Generator
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

# Column definitions
ITEM_EFFECT_COLUMNS = {'id', 'trigger_type', 'id_spell'}
ITEM_X_EFFECT_COLUMNS = {'id', 'id_parent', 'id_item_effect'}

class ItemSpellData(NamedTuple):
    """Structured item spell data for better type safety"""
    item_id: int
    spell_id: int

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

def process_item_effects(effect_data: List[Dict]) -> Dict[int, int]:
    """Process item effects into spell mapping"""
    effects = {}
    
    for row in tqdm(effect_data, desc="Processing item effects"):
        try:
            effect_id = int(row['id'])
            trigger_type = int(row['trigger_type'])
            spell_id = int(row['id_spell'])
            
            # Only process on-use effects (trigger_type = 0)
            if trigger_type == 0 and spell_id > 0:
                effects[effect_id] = spell_id
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid item effect data: {row} - {str(e)}[/yellow]")
            continue
            
    return effects

def process_item_spells(item_data: List[Dict], effects: Dict[int, int]) -> List[ItemSpellData]:
    """Process item to spell mappings"""
    items = []
    
    for row in tqdm(item_data, desc="Processing item spells"):
        try:
            item_id = int(row['id_parent'])
            effect_id = int(row['id_item_effect'])
            
            if item_id > 0 and effect_id in effects:
                items.append(ItemSpellData(item_id, effects[effect_id]))
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid item mapping: {row} - {str(e)}[/yellow]")
            continue
            
    return sorted(items, key=lambda x: x.item_id)

def write_lua_file(output_file: Path, item_data: List[ItemSpellData]) -> None:
    """Optimized Lua file writing with improved string handling"""
    try:
        header = [
            "-- Auto-generated item spell data",
            "-- Format: [ItemID] = SpellID",
            "local ItemSpell = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"ItemSpell = setmetatable({{}}, {{__index = function() return 0 end}})",
            f"-- Estimated item spell entries count: {len(item_data)}",
            ""
        ]
        
        def chunk_generator():
            chunk = []
            items_processed = 0
            
            for data in item_data:
                chunk.append(f"ItemSpell[{data.item_id}] = {data.spell_id}")
                items_processed += 1
                
                if items_processed % CHUNK_SIZE == 0:
                    yield '\n'.join(chunk)
                    chunk = []
                    
                    if items_processed % GC_THRESHOLD == 0:
                        gc.collect()
            
            if chunk:
                yield '\n'.join(chunk)
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(ItemSpell, nil)",
            "",
            "HeroDBC.DBC.ItemSpell = ItemSpell",
            "return ItemSpell"
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for chunk in chunk_generator():
                file.write(chunk + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(item_data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading item effect data...[/cyan]")
    effect_data = mmap_read_csv(generated_dir / 'ItemEffect.csv', ITEM_EFFECT_COLUMNS)
    effects = process_item_effects(effect_data)
    
    console.print("[cyan]Loading item mapping data...[/cyan]")
    item_data = mmap_read_csv(generated_dir / 'ItemXItemEffect.csv', ITEM_X_EFFECT_COLUMNS)
    processed_data = process_item_spells(item_data, effects)
    
    output_file = addon_enum_dir / 'ItemSpell.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
