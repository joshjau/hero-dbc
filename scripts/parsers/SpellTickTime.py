# -*- coding: utf-8 -*-
"""
Spell Tick Time Parser
Processes SpellEffect.csv to generate Lua table of spell tick times
Author: Kutikuti
"""

import sys
import os
import csv
from pathlib import Path  # Using pathlib for better path handling
from tqdm import tqdm  # For progress visualization
from rich.console import Console  # For better error handling and output
from cachetools import cached, TTLCache  # For caching expensive operations

# Initialize rich console for better output formatting
console = Console()

# Cache for expensive file operations with 5 minute TTL
@cached(cache=TTLCache(maxsize=100, ttl=300))
def get_csv_data(file_path):
    """Load and cache CSV data with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            return list(csv.DictReader(csvfile, escapechar='\\'))
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/red]")
        raise

def main():
    # Use pathlib for more robust path handling
    base_dir = Path(sys.path[0]).parent.parent.parent / 'hero-dbc'
    generated_dir = base_dir / 'scripts' / 'DBC' / 'generated'
    addon_enum_dir = base_dir / 'HeroDBC' / 'DBC'

    # Get CSV data with progress indication
    console.print("[cyan]Loading SpellEffect.csv...[/cyan]")
    spell_effect_data = get_csv_data(generated_dir / 'SpellEffect.csv')
    
    # Process data with progress bar
    console.print("[cyan]Processing spell tick times...[/cyan]")
    valid_rows = []
    current_id = 0
    
    # Use tqdm for progress visualization
    for row in tqdm(sorted(spell_effect_data, key=lambda d: int(d['id_parent']))):
        if not int(row['amplitude']) == 0 and current_id != int(row['id_parent']):
            current_id = int(row['id_parent'])
            valid_rows.append(row)

    # Write output file with error handling
    output_file = addon_enum_dir / 'SpellTickTime.lua'
    try:
        with output_file.open('w', encoding='utf-8') as file:
            file.write('HeroDBC.DBC.SpellTickTime = {\n')
            for row in valid_rows:
                file.write(f"  [{row['id_parent']}] = {{ {int(row['amplitude'])}, {'false' if row['id_mechanic'] == '15' else 'true'} }},\n")
            file.write('}\n')
        console.print(f"[green]Successfully wrote {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing {output_file}: {str(e)}[/red]")
        raise

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Script failed: {str(e)}[/red]")
        sys.exit(1)
