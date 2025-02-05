# -*- coding: utf-8 -*-
"""
Optimized Spell Aura Stat Parser
Processes SpellEffect.csv to generate Lua table of aura stat effects
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
BATCH_SIZE = 10000
GC_THRESHOLD = 5000
CPU_COUNT = max(1, min(mp.cpu_count() - 1, 8))

# Spell Effect Constants
EFFECT_TYPE_APPLY_AURA = 6

# Aura Types (SubType in SpellEffect)
AURA_TYPES = {
    29: 'ATTRIBUTE',              # Base stats
    137: 'TOTAL_STAT_PERCENT',    # Total stat %
    189: 'RATING',                # Rating modifications
    193: 'ALL_HASTE_PERCENT',     # Haste %
    290: 'CRIT_PERCENT',          # Crit %
    318: 'MASTERY_PERCENT',       # Mastery %
    471: 'VERSATILITY_PERCENT',   # Vers %
}

# Rating Misc Values (for type 189)
DPS_RATING_MASKS = {
    1792,         # Crit rating
    917504,       # Haste rating
    33554432,     # Mastery rating
    1879048192,   # Versatility rating
}

NEEDED_COLUMNS = {'id_parent', 'type', 'sub_type', 'misc_value_1'}

class AuraData(NamedTuple):
    """Structured aura data for better type safety and memory efficiency"""
    spell_id: int
    is_dps_stat: bool

def is_dps_aura(sub_type: int, misc_value: int) -> bool:
    """Determine if the aura provides DPS stats"""
    if sub_type in AURA_TYPES:
        if sub_type == 189:  # Rating modification
            return misc_value in DPS_RATING_MASKS
        return True
    return False

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

def process_chunk(chunk: List[Dict]) -> List[AuraData]:
    """Process a chunk of spell data in parallel"""
    aura_data = []
    current_spell = None
    
    for row in chunk:
        try:
            spell_id = int(row['id_parent'])
            if spell_id > 0 and spell_id != current_spell:
                effect_type = int(row['type'])
                if effect_type == EFFECT_TYPE_APPLY_AURA:
                    current_spell = spell_id
                    sub_type = int(row['sub_type'])
                    misc_value = int(row['misc_value_1'])
                    is_dps = is_dps_aura(sub_type, misc_value)
                    aura_data.append(AuraData(spell_id, is_dps))
        except (ValueError, KeyError):
            continue
            
    return aura_data

def process_spell_data(spell_data: List[Dict]) -> List[AuraData]:
    """Process spell data with parallel processing"""
    chunk_size = max(100, min(CHUNK_SIZE, len(spell_data) // (CPU_COUNT * 4)))
    chunks = [spell_data[i:i + chunk_size] for i in range(0, len(spell_data), chunk_size)]
    
    with mp.Pool(CPU_COUNT) as pool:
        results = list(tqdm(
            pool.imap(process_chunk, chunks),
            total=len(chunks),
            desc="Processing aura stats"
        ))
    
    return sorted(
        (item for chunk in results for item in chunk),
        key=lambda x: x.spell_id
    )

def write_lua_file(output_file: Path, aura_data: List[AuraData]) -> None:
    """Optimized Lua file writing with improved string handling"""
    try:
        header = [
            "-- Auto-generated spell aura stat data",
            "-- Format: [SpellID] = isDPSStat",
            "-- true = Primary/Secondary stats (DPS)",
            "-- false = Tertiary/Other stats",
            "local SpellAuraStat = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellAuraStat = setmetatable({{}}, {{__index = function() return false end}})",
            f"-- Estimated aura entries count: {len(aura_data)}",
            ""
        ]
        
        def chunk_generator():
            chunk = []
            items_processed = 0
            
            for data in aura_data:
                chunk.append(f"SpellAuraStat[{data.spell_id}] = {str(data.is_dps_stat).lower()}")
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
            "setmetatable(SpellAuraStat, nil)",
            "",
            "HeroDBC.DBC.SpellAuraStat = SpellAuraStat",
            "return SpellAuraStat"
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for chunk in chunk_generator():
                file.write(chunk + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(aura_data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellEffect.csv...[/cyan]")
    spell_data = mmap_read_csv(generated_dir / 'SpellEffect.csv', NEEDED_COLUMNS)
    processed_data = process_spell_data(spell_data)
    
    output_file = addon_enum_dir / 'SpellAuraStat.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
