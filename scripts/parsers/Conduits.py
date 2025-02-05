# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
Optimized Conduits Parser
Processes SoulbindConduit data to generate JSON and Lua output
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

# Column definitions
SPEC_SET_COLUMNS = {'id', 'id_parent', 'id_spec'}
SPELL_NAME_COLUMNS = {'id', 'name'}
CONDUIT_RANK_COLUMNS = {'id_parent', 'id_spell'}
SOULBIND_CONDUIT_COLUMNS = {'id', 'id_spec_set', 'type'}

class ConduitData(NamedTuple):
    """Structured conduit data for better type safety"""
    conduit_id: int
    spell_id: int
    name: str
    specs: List[int]
    conduit_type: int

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
                for line_num, line in enumerate(f, 2):
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

def process_spell_names(spell_data: List[Dict]) -> Dict[int, str]:
    """Process spell names into lookup dictionary"""
    spell_names = {}
    for row in tqdm(spell_data, desc="Processing spell names"):
        try:
            spell_id = int(row['id'])
            name = row['name'].strip()
            if spell_id > 0 and name:
                spell_names[spell_id] = name
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid spell name data: {row} - {str(e)}[/yellow]")
            continue
    return spell_names

def process_spec_sets(spec_data: List[Dict]) -> Dict[str, List[int]]:
    """Process spec sets into lookup dictionary"""
    spec_sets = defaultdict(list)
    for row in tqdm(spec_data, desc="Processing spec sets"):
        try:
            parent_id = row['id_parent']
            spec_id = int(row['id_spec'])
            if spec_id > 0:
                spec_sets[parent_id].append(spec_id)
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid spec set data: {row} - {str(e)}[/yellow]")
            continue
    return dict(spec_sets)

def process_conduits(rank_data: List[Dict], conduit_data: List[Dict], 
                    spell_names: Dict[int, str], spec_sets: Dict[str, List[int]]) -> List[ConduitData]:
    """Process conduit data into final structure"""
    conduits = []
    processed_ids = set()
    
    for row in tqdm(rank_data, desc="Processing conduits"):
        try:
            conduit_id = int(row['id_parent'])
            spell_id = int(row['id_spell'])
            
            if spell_id <= 0 or conduit_id in processed_ids:
                continue
                
            if spell_id not in spell_names:
                continue
                
            # Find corresponding conduit data
            conduit_info = next(
                (c for c in conduit_data if int(c['id']) == conduit_id),
                None
            )
            
            if not conduit_info:
                continue
                
            specs = []
            spec_set_id = conduit_info['id_spec_set']
            if spec_set_id != '0':
                specs = spec_sets.get(spec_set_id, [])
            
            conduits.append(ConduitData(
                conduit_id=conduit_id,
                spell_id=spell_id,
                name=spell_names[spell_id],
                specs=specs,
                conduit_type=int(conduit_info['type'])
            ))
            
            processed_ids.add(conduit_id)
            
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid conduit data: {row} - {str(e)}[/yellow]")
            continue
            
    return sorted(conduits, key=lambda x: x.conduit_id)

def write_json_file(output_file: Path, conduits: List[ConduitData]) -> None:
    """Write JSON output with optimized formatting"""
    try:
        json_data = [
            {
                'conduitId': c.conduit_id,
                'conduitSpellID': c.spell_id,
                'conduitName': c.name,
                'specs': c.specs,
                'conduitType': c.conduit_type
            }
            for c in conduits
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as f:
            json.dump(json_data, f, indent=4, sort_keys=True)
        console.print(f"[green]Successfully wrote conduit data to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def write_lua_file(output_file: Path, conduits: List[ConduitData]) -> None:
    """Write Lua output with optimized formatting"""
    try:
        header = [
            "-- Auto-generated conduit data",
            "-- Format: [ConduitID] = SpellID",
            "local SpellConduits = {}",
            "",
            "-- Pre-allocate known size for better performance",
            f"SpellConduits = setmetatable({{}}, {{__index = function() return 0 end}})",
            f"-- Estimated conduit entries count: {len(conduits)}",
            ""
        ]
        
        def chunk_generator():
            chunk = []
            items_processed = 0
            
            for conduit in conduits:
                chunk.append(f"SpellConduits[{conduit.conduit_id}] = {conduit.spell_id}")
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
            "setmetatable(SpellConduits, nil)",
            "",
            "HeroDBC.DBC.SpellConduits = SpellConduits",
            "return SpellConduits"
        ]
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as file:
            file.write('\n'.join(header))
            for chunk in chunk_generator():
                file.write(chunk + '\n')
            file.write('\n'.join(footer))
            
        console.print(f"[green]Successfully wrote {len(conduits)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    parsed_dir = base_dir / 'scripts' / 'DBC' / 'parsed'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    # Load and process data
    console.print("[cyan]Loading data files...[/cyan]")
    spell_names = process_spell_names(
        mmap_read_csv(generated_dir / 'SpellName.csv', SPELL_NAME_COLUMNS)
    )
    
    spec_sets = process_spec_sets(
        mmap_read_csv(generated_dir / 'SpecSetMember.csv', SPEC_SET_COLUMNS)
    )
    
    conduit_data = mmap_read_csv(generated_dir / 'SoulbindConduit.csv', SOULBIND_CONDUIT_COLUMNS)
    rank_data = mmap_read_csv(generated_dir / 'SoulbindConduitRank.csv', CONDUIT_RANK_COLUMNS)
    
    # Process conduits
    conduits = process_conduits(rank_data, conduit_data, spell_names, spec_sets)
    
    # Write output files
    json_output = parsed_dir / 'Conduits.json'
    lua_output = addon_enum_dir / 'SpellConduits.lua'
    
    write_json_file(json_output, conduits)
    write_lua_file(lua_output, conduits)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
