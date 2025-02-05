# -*- coding: utf-8 -*-
"""
Optimized Spell Duration Parser
Processes SpellDuration.csv and SpellMisc.csv to generate Lua table of spell durations
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
from itertools import islice
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
PANDEMIC_MULTIPLIER = 0.3  # WoW's pandemic duration multiplier
DURATION_PRECISION = 3     # Decimal precision for durations

# Column definitions
DURATION_COLUMNS = {'id', 'duration_1', 'duration_2'}
MISC_COLUMNS = {'id_parent', 'id_duration'}
CPU_COUNT = max(1, min(mp.cpu_count() - 1, 8))

class DurationData(NamedTuple):
    """Structured duration data for better type safety and memory efficiency"""
    spell_id: int
    base_duration: float
    max_duration: float  # Including pandemic

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

def process_duration_data(duration_data: List[Dict]) -> Dict[str, Tuple[float, float]]:
    """Process raw duration data into structured format"""
    durations = {}
    
    for row in tqdm(duration_data, desc="Processing base durations"):
        try:
            duration = float(row['duration_1'])
            if duration > 0:
                duration_id = row['id']
                base_duration = round(duration, DURATION_PRECISION)
                pandemic_duration = round(duration * PANDEMIC_MULTIPLIER, DURATION_PRECISION)
                max_duration = base_duration + pandemic_duration
                durations[duration_id] = (base_duration, max_duration)
        except (ValueError, KeyError):
            continue
    
    return durations

def process_spell_chunk(chunk: List[Dict], durations: Dict[str, Tuple[float, float]]) -> List[DurationData]:
    """Process a chunk of spell data in parallel"""
    spell_data = []
    
    for row in chunk:
        try:
            duration_id = row['id_duration']
            if int(duration_id) > 0 and duration_id in durations:
                spell_id = int(row['id_parent'])
                base_duration, max_duration = durations[duration_id]
                spell_data.append(DurationData(spell_id, base_duration, max_duration))
        except (ValueError, KeyError):
            continue
            
    return spell_data

def process_spell_misc_data(misc_data: List[Dict], durations: Dict[str, Tuple[float, float]]) -> List[DurationData]:
    """Process spell misc data with parallel processing"""
    chunk_size = max(100, min(CHUNK_SIZE, len(misc_data) // (CPU_COUNT * 4)))
    chunks = [misc_data[i:i + chunk_size] for i in range(0, len(misc_data), chunk_size)]
    
    process_chunk_with_durations = partial(process_spell_chunk, durations=durations)
    
    with mp.Pool(CPU_COUNT) as pool:
        results = list(tqdm(
            pool.imap(process_chunk_with_durations, chunks),
            total=len(chunks),
            desc="Processing spell durations"
        ))
    
    return sorted(
        (item for chunk in results for item in chunk),
        key=lambda x: x.spell_id
    )

def write_lua_file(output_file: Path, duration_data: List[DurationData]) -> None:
    """Optimized Lua file writing with improved string handling"""
    try:
        header = [
            "-- Auto-generated spell duration data",
            "-- Format: [SpellID] = { BaseDuration, MaxDuration }",
            "-- MaxDuration includes pandemic duration (30% of base)",
            "local SpellDuration = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellDuration = setmetatable({{}}, {{__index = function() return {{0, 0}} end}})",
            f"-- Estimated duration entries count: {len(duration_data)}",
            ""
        ]
        
        entry_template = "SpellDuration[{0}] = {{{1:.{3}f}, {2:.{3}f}}}"
        
        def chunk_generator():
            chunk = []
            items_processed = 0
            
            for data in duration_data:
                chunk.append(entry_template.format(
                    data.spell_id,
                    data.base_duration,
                    data.max_duration,
                    DURATION_PRECISION
                ))
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
            "setmetatable(SpellDuration, nil)",
            "",
            "HeroDBC.DBC.SpellDuration = SpellDuration",
            "return SpellDuration"
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for chunk in chunk_generator():
                file.write(chunk + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(duration_data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellDuration.csv...[/cyan]")
    duration_data = mmap_read_csv(generated_dir / 'SpellDuration.csv', DURATION_COLUMNS)
    durations = process_duration_data(duration_data)

    console.print("[cyan]Loading SpellMisc.csv...[/cyan]")
    misc_data = mmap_read_csv(generated_dir / 'SpellMisc.csv', MISC_COLUMNS)
    processed_data = process_spell_misc_data(misc_data, durations)
    
    output_file = addon_enum_dir / 'SpellDuration.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
