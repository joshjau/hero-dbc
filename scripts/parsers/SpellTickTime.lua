# -*- coding: utf-8 -*-
"""
Optimized Spell Tick Time Parser
Processes SpellEffect.csv to generate Lua table of spell tick times
Author: Kutikuti
"""

import sys
import os
import csv
from pathlib import Path
from tqdm import tqdm
from rich.console import Console
from cachetools import cached, TTLCache
from typing import List, Dict
import itertools

# Initialize rich console for better output formatting
console = Console()

# Cache for expensive file operations with 5 minute TTL
@cached(cache=TTLCache(maxsize=100, ttl=300))
def load_csv_data(file_path: Path) -> List[Dict]:
    """Load and cache CSV data with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            return list(csv.DictReader(csvfile, escapechar='\\'))
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_spell_data(csv_data: List[Dict]) -> List[Dict]:
    """
    Process CSV data and return sorted valid rows
    Uses optimized grouping for faster processing
    """
    valid_rows = []
    
    # Group by parent ID for more efficient processing
    sorted_data = sorted(csv_data, key=lambda d: int(d['id_parent']))
    grouped_data = itertools.groupby(sorted_data, key=lambda d: int(d['id_parent']))
    
    # Process data with progress visualization
    with tqdm(desc="Processing spell tick times") as pbar:
        for parent_id, group in grouped_data:
            group_data = list(group)
            for row in group_data:
                amplitude = int(row['amplitude'])
                if amplitude != 0:
                    valid_rows.append({
                        'id': parent_id,
                        'amplitude': amplitude,
                        'mechanic': row['id_mechanic'] != "15",
                        'effect_type': int(row.get('id_effect', 0))  # Added effect type for better filtering
                    })
                    break  # Only need first valid amplitude per spell
            pbar.update(len(group_data))
    
    return valid_rows

def write_lua_file(output_file: Path, data: List[Dict]) -> None:
    """
    Write processed data to Lua file with optimized structure
    Generates a more efficient Lua table format
    """
    try:
        with output_file.open('w', encoding='utf-8') as file:
            file.write("-- Auto-generated spell tick time data\n")
            file.write("-- Format: [spellID] = {amplitude, hasMechanic}\n")
            file.write("local SpellTickTime = {\n")
            
            # Sort by ID for better Lua table performance
            sorted_data = sorted(data, key=lambda x: x['id'])
            
            # Use string concatenation for better performance
            table_entries = []
            for entry in sorted_data:
                table_entries.append(
                    f"  [{entry['id']}]={{" 
                    f"{entry['amplitude']},"
                    f"{str(entry['mechanic']).lower()}}}"
                )
            
            file.write(',\n'.join(table_entries))
            file.write("\n}\n\n")
            
            # Add return statement for better Lua module structure
            file.write("HeroDBC.DBC.SpellTickTime = SpellTickTime\n")
            file.write("return SpellTickTime\n")
            
        console.print(f"[green]Successfully wrote {len(data)} entries to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    console.print("[cyan]Loading SpellEffect.csv...[/cyan]")
    spell_effect_data = load_csv_data(generated_dir / 'SpellEffect.csv')
    
    processed_data = process_spell_data(spell_effect_data)
    
    output_file = addon_enum_dir / 'SpellTickTime.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1) 