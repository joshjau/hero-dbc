# -*- coding: utf-8 -*-
"""
Optimized Soulbinds Parser
Processes Covenant and Soulbind data to generate JSON output
Author: Kutikuti
"""

import sys
import gc
from pathlib import Path
from typing import Dict, List, Set, NamedTuple, Generator
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

# Column definitions for each CSV
COVENANT_COLUMNS = {'id', 'name'}
SOULBIND_COLUMNS = {'id', 'name', 'id_covenant', 'id_garr_talent_tree'}
GARR_TALENT_COLUMNS = {'id', 'name', 'id_garr_talent_tree', 'conduit_type', 'id_garr_talent_prereq', 'tier', 'ui_order'}
GARR_TALENT_RANK_COLUMNS = {'id_parent', 'id_spell'}
SPELL_NAME_COLUMNS = {'id', 'name'}

class SoulbindData(NamedTuple):
    """Structured soulbind data for better type safety"""
    soulbind_id: int
    name: str
    tree_id: int
    covenant_id: int

class TalentData(NamedTuple):
    """Structured talent data"""
    talent_id: int
    name: str
    tree_id: int
    conduit_type: int
    prereq_id: int
    tier: int
    ui_order: int

def mmap_read_csv(file_path: Path, needed_columns: Set[str]) -> List[Dict]:
    """Memory-mapped CSV reading with optimized buffer size and encoding fallbacks"""
    # Extended encodings list to handle more cases
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    for encoding in encodings:
        try:
            # First try reading normally to validate encoding
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                # Read and process header
                header = CSV_PATTERN.split(f.readline().strip())
                col_indices = {col: idx for idx, col in enumerate(header) if col in needed_columns}
                
                if not all(col in col_indices for col in needed_columns):
                    missing = needed_columns - set(col_indices.keys())
                    raise ValueError(f"Missing required columns: {missing}")
                
                # Read data rows (skip header)
                rows = []
                for line_num, line in enumerate(f, 2):  # Start at 2 since we already read header
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
                        console.print(f"[yellow]Warning: Skipping malformed line {line_num} due to: {str(e)}[/yellow]")
                        continue
                
                return rows
                    
        except UnicodeDecodeError:
            continue  # Try next encoding
        except Exception as e:
            console.print(f"[red]Error reading {file_path} with {encoding}: {str(e)}[/red]")
            continue
            
    raise UnicodeDecodeError(f"Failed to decode {file_path} with any known encoding")

def read_csv_rows(mm: mmap.mmap, col_indices: Dict[str, int], header_len: int, encoding: str) -> Generator[Dict, None, None]:
    """Generator function for memory-efficient CSV reading with specified encoding"""
    items_processed = 0
    
    while True:
        line = mm.readline()
        if not line:
            break
        
        try:
            values = CSV_PATTERN.split(line.decode(encoding).strip())
            if len(values) >= header_len:
                yield {col: values[idx] for col, idx in col_indices.items()}
                
                items_processed += 1
                if items_processed % GC_THRESHOLD == 0:
                    gc.collect()
        except UnicodeDecodeError as e:
            console.print(f"[yellow]Warning: Skipping malformed line due to encoding issue[/yellow]")
            continue

def process_spell_names(spell_data: List[Dict]) -> Dict[str, str]:
    """Process spell names into lookup dictionary with improved error handling"""
    spell_names = {}
    for row in spell_data:
        try:
            spell_id = str(row.get('id', '')).strip()
            name = str(row.get('name', '')).strip()
            if spell_id and name:
                spell_names[spell_id] = name
        except (ValueError, AttributeError) as e:
            console.print(f"[yellow]Warning: Invalid spell name data: {row} - {str(e)}[/yellow]")
            continue
    return spell_names

def process_talent_ranks(rank_data: List[Dict]) -> Dict[int, int]:
    """Process talent ranks into spell mapping with improved error handling"""
    tree_spells = {}
    for row in rank_data:
        try:
            # Safely convert string values to integers with validation
            parent_id = row.get('id_parent', '0').strip()
            spell_id = row.get('id_spell', '0').strip()
            
            if parent_id.isdigit() and spell_id.isdigit():
                parent_id_int = int(parent_id)
                spell_id_int = int(spell_id)
                if spell_id_int > 0 and parent_id_int > 0:
                    tree_spells[parent_id_int] = spell_id_int
        except (ValueError, AttributeError) as e:
            console.print(f"[yellow]Warning: Invalid talent rank data: {row} - {str(e)}[/yellow]")
            continue
    return tree_spells

def process_talents(talent_data: List[Dict], tree_spells: Dict[int, int], spell_names: Dict[str, str]) -> Dict[int, Dict]:
    """Process talents into structured format with improved error handling"""
    talent_trees = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # Changed to nested defaultdict
    
    for row in tqdm(talent_data, desc="Processing talents"):
        try:
            # Safely convert string values to integers with validation
            talent_id = int(str(row.get('id', '0')).strip())
            tree_id = int(str(row.get('id_garr_talent_tree', '0')).strip())
            tier = int(str(row.get('tier', '0')).strip())
            ui_order = int(str(row.get('ui_order', '0')).strip())
            
            if talent_id <= 0 or tree_id <= 0:
                continue  # Skip invalid IDs
            
            ability = {
                'soulbindAbilityId': talent_id,
                'soulbindAbilityName': row.get('name', '').strip()
            }
            
            # Add spell data if available
            if talent_id in tree_spells:
                spell_id = tree_spells[talent_id]
                ability['soulbindAbilitySpellId'] = spell_id
                spell_name = spell_names.get(str(spell_id))
                if spell_name:
                    ability['soulbindAbilityName'] = spell_name.strip()
            
            # Add optional fields with validation
            try:
                conduit_type = int(str(row.get('conduit_type', '0')).strip())
                if conduit_type > 0:
                    ability['soulbindAbilityConduitType'] = conduit_type
            except ValueError:
                pass
                
            try:
                prereq_id = int(str(row.get('id_garr_talent_prereq', '0')).strip())
                if prereq_id > 0:
                    ability['soulbindAbilityPrereq'] = prereq_id
            except ValueError:
                pass
            
            # Ensure we preserve the exact structure
            talent_trees[tree_id][tier][ui_order] = ability
            
            # Debug output to track what's being processed
            console.print(f"[cyan]Added talent: Tree {tree_id}, Tier {tier}, Order {ui_order}, Name: {ability['soulbindAbilityName']}[/cyan]")
            
        except (ValueError, KeyError, TypeError) as e:
            console.print(f"[yellow]Warning: Skipping talent due to {str(e)}: {row}[/yellow]")
            continue
            
    return dict(talent_trees)  # Convert defaultdict to regular dict for JSON serialization

def process_soulbinds(soulbind_data: List[Dict], talent_trees: Dict[int, Dict]) -> List[Dict]:
    """Process soulbinds into final structure"""
    soulbinds = []
    
    for row in tqdm(soulbind_data, desc="Processing soulbinds"):
        try:
            soulbind = {
                'soulbindId': int(row['id']),
                'soulbindName': row['name'],
                'soulbindTreeID': int(row['id_garr_talent_tree']),
                'soulbindTree': talent_trees.get(int(row['id_garr_talent_tree']), {})
            }
            soulbinds.append(soulbind)
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Skipping soulbind due to {e}[/yellow]")
            continue
            
    return sorted(soulbinds, key=lambda x: x['soulbindId'])

def process_covenants(covenant_data: List[Dict], soulbinds: List[Dict], soulbind_data: List[Dict]) -> List[Dict]:
    """Process covenants into final structure with improved error handling"""
    # First, create a mapping of soulbind ID to covenant ID from the Soulbind.csv data
    soulbind_covenant_map = {}
    for row in soulbind_data:  # Now we have the soulbind_data parameter
        try:
            soulbind_id = int(row['id'])
            covenant_id = int(row['id_covenant'])
            if soulbind_id > 0 and covenant_id > 0:
                soulbind_covenant_map[soulbind_id] = covenant_id
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Invalid soulbind mapping: {row} - {str(e)}[/yellow]")
            continue

    # Group soulbinds by covenant
    covenant_map = defaultdict(list)
    for soulbind in soulbinds:
        try:
            soulbind_id = soulbind['soulbindId']
            covenant_id = soulbind_covenant_map.get(soulbind_id)
            if covenant_id:
                covenant_map[covenant_id].append(soulbind)
        except (KeyError, TypeError) as e:
            console.print(f"[yellow]Warning: Could not map soulbind {soulbind.get('soulbindId', 'unknown')}: {str(e)}[/yellow]")
            continue

    # Create final covenant structure
    covenants = []
    for row in tqdm(covenant_data, desc="Processing covenants"):
        try:
            covenant_id = int(row['id'])
            covenant = {
                'covenantId': covenant_id,
                'covenantName': row['name'],
                'soulbinds': covenant_map.get(covenant_id, [])
            }
            covenants.append(covenant)
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]Warning: Skipping covenant due to {e}: {row}[/yellow]")
            continue
            
    return sorted(covenants, key=lambda x: x['covenantId'])

def write_json_file(output_file: Path, data: List[Dict]) -> None:
    """Write JSON output with optimized formatting"""
    try:
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, sort_keys=True)
        console.print(f"[green]Successfully wrote soulbind data to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    parsed_dir = base_dir / 'scripts' / 'DBC' / 'parsed'
    
    # Load all required data
    console.print("[cyan]Loading CSV files...[/cyan]")
    spell_names = process_spell_names(
        mmap_read_csv(generated_dir / 'SpellName.csv', SPELL_NAME_COLUMNS)
    )
    
    tree_spells = process_talent_ranks(
        mmap_read_csv(generated_dir / 'GarrTalentRank.csv', GARR_TALENT_RANK_COLUMNS)
    )
    
    talent_trees = process_talents(
        mmap_read_csv(generated_dir / 'GarrTalent.csv', GARR_TALENT_COLUMNS),
        tree_spells,
        spell_names
    )
    
    soulbinds = process_soulbinds(
        mmap_read_csv(generated_dir / 'Soulbind.csv', SOULBIND_COLUMNS),
        talent_trees
    )
    
    covenants = process_covenants(
        mmap_read_csv(generated_dir / 'Covenant.csv', COVENANT_COLUMNS),
        soulbinds,
        mmap_read_csv(generated_dir / 'Soulbind.csv', SOULBIND_COLUMNS)
    )
    
    # Write output
    output_file = parsed_dir / 'Soulbinds.json'
    write_json_file(output_file, covenants)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)