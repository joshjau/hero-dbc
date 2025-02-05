# -*- coding: utf-8 -*-
"""
Optimized Azerite Power Parser
Processes Azerite Power data to generate JSON outputs
Author: Quentin Giraud <dev@aethys.io>
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
AZERITE_POWER_COLUMNS = {'id', 'id_spell', 'id_spec_set_member'}
POWER_SET_MEMBER_COLUMNS = {'id', 'id_parent', 'id_power', 'class_id', 'tier', 'index'}
ITEM_SPARSE_COLUMNS = {'id'}
EMPOWERED_ITEM_COLUMNS = {'id', 'id_item', 'id_power_set', 'id_azerite_tier_unlock'}
SPELL_NAME_COLUMNS = {'id', 'name'}
TIER_UNLOCK_COLUMNS = {'id', 'id_parent', 'tier', 'azerite_level'}
SPEC_SET_MEMBER_COLUMNS = {'id', 'id_parent', 'id_spec'}

class AzeritePowerData(NamedTuple):
    """Structured azerite power data"""
    power_id: int
    spell_id: int
    spell_name: str
    specs: List[int]
    tier: int
    classes: List[int]

class AzeriteItemData(NamedTuple):
    """Structured azerite item data"""
    item_id: int
    tiers: List[Dict[str, int]]

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

def load_specs_whitelist(file_path: Path) -> Dict[str, List[int]]:
    """Load specs whitelist with validation"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            whitelist = json.load(f)
        return {str(k): v for k, v in whitelist.items()}
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load specs whitelist: {str(e)}[/yellow]")
        return {}

def process_valid_power_sets(empowered_items: List[Dict], items: List[Dict]) -> Dict[str, Dict]:
    """Process valid azerite power sets"""
    valid_sets = {}
    item_ids = {row['id'] for row in items}
    
    for item in tqdm(empowered_items, desc="Processing power sets"):
        try:
            if item['id_item'] in item_ids:
                valid_sets[item['id_power_set']] = item
        except (KeyError, ValueError) as e:
            console.print(f"[yellow]Warning: Invalid power set data: {item} - {str(e)}[/yellow]")
            continue
            
    console.print(f"[green]Found {len(valid_sets)} valid power sets out of {len(empowered_items)} possible[/green]")
    return valid_sets

def process_valid_powers(power_set_members: List[Dict], valid_sets: Dict[str, Dict],
                        powers: List[Dict], spell_names: List[Dict]) -> Dict[str, Dict]:
    """Process valid azerite powers"""
    valid_powers = {}
    spell_name_map = {row['id']: row['name'] for row in spell_names}
    
    for member in tqdm(power_set_members, desc="Processing powers"):
        try:
            if member['id_parent'] not in valid_sets:
                continue
                
            power_id = member['id_power']
            if power_id not in {p['id'] for p in powers}:
                continue
                
            power = next(p for p in powers if p['id'] == power_id)
            spell_id = power['id_spell']
            
            if spell_id == '0' or spell_id not in spell_name_map:
                continue
                
            valid_powers[power_id] = power
                
        except (KeyError, ValueError) as e:
            console.print(f"[yellow]Warning: Invalid power data: {member} - {str(e)}[/yellow]")
            continue
            
    console.print(f"[green]Found {len(valid_powers)} valid powers out of {len(powers)} possible[/green]")
    return valid_powers

def process_power_specs(power: Dict, spec_members: List[Dict], specs_whitelist: Dict[str, List[int]]) -> List[int]:
    """Process specs for a power"""
    specs = []
    spec_set_id = power.get('id_spec_set_member', '0')
    
    if spec_set_id != '0':
        specs.extend(
            int(member['id_spec'])
            for member in spec_members
            if member['id_parent'] == spec_set_id
        )
        
    power_id = power.get('id')
    if power_id in specs_whitelist:
        specs.extend(specs_whitelist[power_id])
        
    return sorted(set(specs))

def process_tier_unlocks(item: Dict, tier_unlocks: List[Dict]) -> List[Dict[str, int]]:
    """Process tier unlocks for an item"""
    unlock_id = item.get('id_azerite_tier_unlock')
    if not unlock_id:
        return []
        
    return [
        {
            'tier': int(unlock['tier']),
            'azerite_level': int(unlock['azerite_level'])
        }
        for unlock in tier_unlocks
        if unlock['id_parent'] == unlock_id
    ]

def write_json_file(output_file: Path, data: List[Dict], with_items: bool = True) -> None:
    """Write JSON output with optimized formatting"""
    try:
        if not with_items:
            # Process data for non-items version
            for power in data:
                if power.get('sets'):
                    classes = sorted(set(
                        set_data['classId']
                        for set_data in power['sets']
                        if 'classId' in set_data
                    ))
                    power['classesId'] = classes
                    
                    # Get first valid tier
                    for set_data in power['sets']:
                        if 'tier' in set_data:
                            power['tier'] = set_data['tier']
                            break
                            
                    del power['sets']
        
        with output_file.open('w', encoding='utf-8', buffering=BUFFER_SIZE) as f:
            json.dump(data, f, indent=4, sort_keys=True)
        console.print(f"[green]Successfully wrote azerite power data to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    parsed_dir = base_dir / 'scripts' / 'DBC' / 'parsed'
    specs_whitelist_file = base_dir / 'scripts' / 'parsers' / 'AzeritePowerSpecsWhitelist.json'

    # Check if Azerite system exists in current game version
    if not (generated_dir / 'AzeriteEmpoweredItem.csv').exists():
        console.print("[yellow]Azerite system not present in current game version - skipping[/yellow]")
        
        # Write empty data files to maintain structure
        empty_data = []
        write_json_file(parsed_dir / 'AzeritePowerWithItems.json', empty_data, True)
        write_json_file(parsed_dir / 'AzeritePower.json', empty_data, False)
        return

    # Load specs whitelist
    specs_whitelist = load_specs_whitelist(specs_whitelist_file)

    # Load all required data
    console.print("[cyan]Loading data files...[/cyan]")
    empowered_items = mmap_read_csv(generated_dir / 'AzeriteEmpoweredItem.csv', EMPOWERED_ITEM_COLUMNS)
    items = mmap_read_csv(generated_dir / 'ItemSparse.csv', ITEM_SPARSE_COLUMNS)
    
    # Process valid power sets
    valid_sets = process_valid_power_sets(empowered_items, items)
    
    # Process valid powers
    power_set_members = mmap_read_csv(generated_dir / 'AzeritePowerSetMember.csv', POWER_SET_MEMBER_COLUMNS)
    powers = mmap_read_csv(generated_dir / 'AzeritePower.csv', AZERITE_POWER_COLUMNS)
    spell_names = mmap_read_csv(generated_dir / 'SpellName.csv', SPELL_NAME_COLUMNS)
    
    valid_powers = process_valid_powers(power_set_members, valid_sets, powers, spell_names)
    
    # Process additional data
    spec_members = mmap_read_csv(generated_dir / 'SpecSetMember.csv', SPEC_SET_MEMBER_COLUMNS)
    tier_unlocks = mmap_read_csv(generated_dir / 'AzeriteTierUnlock.csv', TIER_UNLOCK_COLUMNS)
    
    # Generate final data structure
    azerite_powers = []
    for power_id, power in tqdm(valid_powers.items(), desc="Generating final data"):
        try:
            power_data = {
                'powerId': int(power_id),
                'spellId': int(power['id_spell']),
                'spellName': next(s['name'] for s in spell_names if s['id'] == power['id_spell']),
                'specs': process_power_specs(power, spec_members, specs_whitelist)
            }
            
            # Process sets data
            power_sets = []
            for member in power_set_members:
                if member['id_power'] == power_id:
                    set_data = {
                        'classId': int(member['class_id']),
                        'tier': int(member['tier']),
                        'index': int(member['index'])
                    }
                    
                    # Process items
                    items = []
                    for item in empowered_items:
                        if item['id_power_set'] == member['id_parent']:
                            item_data = {
                                'itemId': int(item['id_item']),
                                'tiers': process_tier_unlocks(item, tier_unlocks)
                            }
                            items.append(item_data)
                    
                    if items:
                        set_data['items'] = items
                        power_sets.append(set_data)
            
            if power_sets:
                power_data['sets'] = power_sets
                azerite_powers.append(power_data)
                
        except Exception as e:
            console.print(f"[yellow]Warning: Error processing power {power_id}: {str(e)}[/yellow]")
            continue
    
    # Write both output versions
    write_json_file(parsed_dir / 'AzeritePowerWithItems.json', azerite_powers, True)
    write_json_file(parsed_dir / 'AzeritePower.json', azerite_powers, False)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
