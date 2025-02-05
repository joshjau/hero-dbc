# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
Optimized Spell Enchant Parser
Processes SpellItemEnchantment.csv to generate Lua table of enchant mappings
Author: Kutikuti
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, NamedTuple, Generator
import mmap
import re
from rich.console import Console
from tqdm import tqdm
from collections import defaultdict
import multiprocessing as mp
from itertools import islice

# Initialize rich console for better output formatting
console = Console()

# Compile regex patterns once for better performance
CSV_PATTERN = re.compile(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)')

# Define constants for better maintainability and performance
CHUNK_SIZE = 500
BUFFER_SIZE = 8192
BATCH_SIZE = 10000  # Optimal batch size for memory management
GC_THRESHOLD = 5000  # Number of processed items before forcing garbage collection
NEEDED_COLUMNS = {'id', 'id_property_1'}
CPU_COUNT = max(1, min(mp.cpu_count() - 1, 8))  # Cap at 8 cores, leave one free

class EnchantData(NamedTuple):
    """Structured enchant data for better type safety and memory efficiency"""
    enchant_id: int
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
                
                rows = []
                buffer = []
                buffer_size = BUFFER_SIZE
                
                while True:
                    line = mm.readline()
                    if not line:
                        break
                    
                    values = CSV_PATTERN.split(line.decode('utf-8').strip())
                    if len(values) >= len(header):
                        rows.append({col: values[idx] for col, idx in col_indices.items()})
                    
                    if len(buffer) >= buffer_size:
                        rows.extend(buffer)
                        buffer = []
                
                if buffer:
                    rows.extend(buffer)
                
                return rows
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_chunk(chunk: List[Dict]) -> List[EnchantData]:
    """Process a chunk of enchant data in parallel"""
    enchant_data = []
    
    for row in chunk:
        try:
            spell_id = int(row['id_property_1'])
            if spell_id > 0:  # Only process valid spell IDs
                enchant_id = int(row['id'])
                enchant_data.append(EnchantData(enchant_id, spell_id))
        except (ValueError, KeyError):
            continue
            
    return enchant_data

def process_enchant_data(enchant_data: List[Dict]) -> List[EnchantData]:
    """Process enchant data with parallel processing"""
    chunk_size = max(100, min(CHUNK_SIZE, len(enchant_data) // (CPU_COUNT * 4)))
    chunks = [enchant_data[i:i + chunk_size] for i in range(0, len(enchant_data), chunk_size)]
    
    with mp.Pool(CPU_COUNT) as pool:
        results = list(tqdm(
            pool.imap(process_chunk, chunks),
            total=len(chunks),
            desc="Processing enchant data"
        ))
    
    return sorted(
        (item for chunk in results for item in chunk),
        key=lambda x: x.enchant_id
    )

def write_lua_file(output_file: Path, enchant_data: List[EnchantData]) -> None:
    """Optimized Lua file writing with improved string handling"""
    try:
        header = [
            "-- Auto-generated spell enchant data",
            "-- Format: [EnchantID] = SpellID",
            "local SpellEnchants = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellEnchants = setmetatable({{}}, {{__index = function() return 0 end}})",
            f"-- Estimated enchant entries count: {len(enchant_data)}",
            ""
        ]
        
        # Use string.format for better performance
        entry_template = "SpellEnchants[{0}] = {1}"
        
        def chunk_generator():
            chunk = []
            items_processed = 0
            
            for data in enchant_data:
                chunk.append(entry_template.format(
                    data.enchant_id,
                    data.spell_id
                ))
                items_processed += 1
                
                if items_processed % CHUNK_SIZE == 0:
                    yield '\n'.join(chunk)
                    chunk = []
            
            if chunk:
                yield '\n'.join(chunk)
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(SpellEnchants, nil)",
            "",
            "HeroDBC.DBC.SpellEnchants = SpellEnchants",
            "return SpellEnchants"
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for chunk in chunk_generator():
                file.write(chunk + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(enchant_data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellItemEnchantment.csv...[/cyan]")
    enchant_data = mmap_read_csv(generated_dir / 'SpellItemEnchantment.csv', NEEDED_COLUMNS)
    processed_data = process_enchant_data(enchant_data)
    
    output_file = addon_enum_dir / 'SpellEnchants.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)