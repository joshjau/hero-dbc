# -*- coding: utf-8 -*-
"""
Optimized Spell GCD Parser
Processes SpellCooldowns.csv to generate Lua table of GCD values
Author: Quentin Giraud <dev@aethys.io>
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
NEEDED_COLUMNS = {'id_parent', 'gcd_cooldown'}
CPU_COUNT = max(1, min(mp.cpu_count() - 1, 8))  # Cap at 8 cores, leave one free

# GCD-specific constants
MIN_VALID_GCD = 0.0    # Minimum valid GCD value
MAX_VALID_GCD = 1.5    # Maximum reasonable GCD value in seconds (most spells are 1.5 or less)
DEFAULT_GCD = 0.0      # Default GCD for unknown spells
GCD_PRECISION = 3      # Number of decimal places for GCD values

# Update these constants
GCD_RANGES = {
    'INSTANT': (0.0, 0.0),      # No GCD
    'FAST': (0.1, 0.25),        # Quick cast abilities
    'NORMAL': (0.5, 1.5),       # Standard GCD abilities
    'CHANNEL': (2.0, 20.0),     # Channeled spells
    'COOLDOWN': (30.0, 180.0),  # Long cooldown abilities
    'MAJOR_CD': (181.0, 2000.0) # Major cooldowns (like raid abilities, special items)
}

class GCDData(NamedTuple):
    """Structured GCD data for better type safety and memory efficiency"""
    spell_id: int
    gcd: float

def validate_gcd(gcd: float) -> bool:
    """
    Validate GCD value within known ranges
    Returns True if the GCD falls into any valid category
    """
    if gcd == 0:  # No GCD
        return True
        
    # Check if GCD falls into any valid range
    return any(
        min_val <= gcd <= max_val 
        for min_val, max_val in GCD_RANGES.values()
    )

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
            
            # Periodic garbage collection for memory management
            items_processed += 1
            if items_processed % GC_THRESHOLD == 0:
                gc.collect()

def mmap_read_csv(file_path: Path, needed_columns: Set[str]) -> List[Dict]:
    """
    Memory-mapped CSV reading with optimized buffer size and generator-based processing
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
                
                # Use generator for memory-efficient reading
                return list(read_csv_rows(mm, col_indices, len(header)))
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_chunk(chunk: List[Dict]) -> List[GCDData]:
    """Process a chunk of spell data in parallel with enhanced validation"""
    gcd_data = []
    
    for row in chunk:
        try:
            spell_id = int(row['id_parent'])
            gcd = float(row['gcd_cooldown'])
            
            # Convert to seconds if in milliseconds
            if gcd > MAX_VALID_GCD:
                gcd = gcd / 1000.0
            
            # Enhanced validation
            if spell_id > 0:
                # Round to specified precision
                gcd = round(gcd, GCD_PRECISION)
                if validate_gcd(gcd):
                    gcd_data.append(GCDData(spell_id, gcd))
                # Only warn about truly impossible values
                elif gcd > 2000.0:
                    console.print(f"[yellow]Warning: Impossible GCD value {gcd} for spell {spell_id}[/yellow]")
        except (ValueError, KeyError):
            continue
            
    return gcd_data

def batch_generator(data: List[Dict], batch_size: int) -> Generator[List[Dict], None, None]:
    """Memory efficient batch generator"""
    iterator = iter(data)
    while batch := list(islice(iterator, batch_size)):
        yield batch
        if len(batch) < batch_size:
            break

def process_spell_data(spell_data: List[Dict]) -> List[GCDData]:
    """Process spell data with parallel processing and memory optimization"""
    # Calculate optimal chunk size based on data size and CPU count
    chunk_size = max(100, min(CHUNK_SIZE, len(spell_data) // (CPU_COUNT * 4)))
    
    # Use generator for memory-efficient chunking
    chunks = batch_generator(spell_data, chunk_size)
    total_chunks = (len(spell_data) + chunk_size - 1) // chunk_size
    
    # Process chunks in parallel with progress tracking
    with mp.Pool(CPU_COUNT) as pool:
        results = list(tqdm(
            pool.imap(process_chunk, chunks),
            total=total_chunks,
            desc="Processing GCD data"
        ))
    
    # Efficiently combine and sort results
    return sorted(
        (item for chunk in results for item in chunk),
        key=lambda x: x.spell_id
    )

def write_lua_file(output_file: Path, gcd_data: List[GCDData]) -> None:
    """
    Optimized Lua file writing with improved string handling and memory efficiency
    """
    try:
        header = [
            "-- Auto-generated spell GCD data",
            "-- Format: [SpellID] = GCDDuration",
            "local SpellGCD = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellGCD = setmetatable({{}}, {{__index = function() return {DEFAULT_GCD} end}})",
            f"-- Estimated GCD entries count: {len(gcd_data)}",
            ""
        ]
        
        # Use format strings for better performance
        entry_template = "SpellGCD[{0}] = {1:.%df}" % GCD_PRECISION
        
        # Process entries in optimized chunks with string joining
        def chunk_generator():
            chunk = []
            items_processed = 0
            
            for data in gcd_data:
                chunk.append(entry_template.format(data.spell_id, data.gcd))
                items_processed += 1
                
                if items_processed % CHUNK_SIZE == 0:
                    yield '\n'.join(chunk)
                    chunk = []
                    
                    # Periodic garbage collection
                    if items_processed % GC_THRESHOLD == 0:
                        gc.collect()
            
            if chunk:
                yield '\n'.join(chunk)
        
        footer = [
            "",
            "-- Freeze the table for security and performance",
            "setmetatable(SpellGCD, nil)",
            "",
            "HeroDBC.DBC.SpellGCD = SpellGCD",
            "return SpellGCD"
        ]
        
        # Write with optimized buffering
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for chunk in chunk_generator():
                file.write(chunk + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(gcd_data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellCooldowns.csv...[/cyan]")
    spell_data = mmap_read_csv(generated_dir / 'SpellCooldowns.csv', NEEDED_COLUMNS)
    gcd_data = process_spell_data(spell_data)
    
    output_file = addon_enum_dir / 'SpellGCD.lua'
    write_lua_file(output_file, gcd_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
