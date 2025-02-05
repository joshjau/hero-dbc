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

# Initialize rich console for better output formatting
console = Console()

# Cache for expensive file operations with 5 minute TTL
@cached(cache=TTLCache(maxsize=100, ttl=300))
def load_csv_data(file_path):
    """Load and cache CSV data with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            return list(csv.DictReader(csvfile, escapechar='\\'))
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def process_spell_data(csv_data):
    """Process CSV data and return sorted valid rows"""
    valid_rows = []
    current_id = 0
    
    # Sort data by parent ID to optimize processing
    sorted_data = sorted(csv_data, key=lambda d: int(d['id_parent']))
    
    # Process data with progress visualization
    for row in tqdm(sorted_data, desc="Processing spell tick times"):
        amplitude = int(row['amplitude'])
        if amplitude != 0 and current_id != int(row['id_parent']):
            current_id = int(row['id_parent'])
            valid_rows.append({
                'id': current_id,
                'amplitude': amplitude,
                'mechanic': row['id_mechanic'] != "15"
            })
    
    return valid_rows

def write_lua_file(output_file, data):
    """Write processed data to Lua file with error handling"""
    try:
        with output_file.open('w', encoding='utf-8') as file:
            # Write optimized Lua table structure
            file.write("-- Auto-generated spell tick time data\n")
            file.write("HeroDBC.DBC.SpellTickTime = {\n")
            
            for entry in data:
                file.write(f"  [{entry['id']}] = {{ {entry['amplitude']}, {str(entry['mechanic']).lower()} }},\n")
            
            file.write("}\n")
        console.print(f"[green]Successfully wrote {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

def main():
    # Use pathlib for more robust path handling
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    # Get CSV data with progress indication
    console.print("[cyan]Loading SpellEffect.csv...[/cyan]")
    spell_effect_data = load_csv_data(generated_dir / 'SpellEffect.csv')
    
    # Process data
    processed_data = process_spell_data(spell_effect_data)
    
    # Write output file
    output_file = addon_enum_dir / 'SpellTickTime.lua'
    write_lua_file(output_file, processed_data)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
