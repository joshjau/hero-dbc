# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>

Modified by: Hero Team
Changes: Enhanced parser with improved validation, caching, and error handling using pandas
"""

import sys
import os
from pathlib2 import Path
import pandas as pd
import ujson as json
from typing import Dict, Any, Tuple, Optional
from rich.console import Console
from rich.progress import track
from cachetools import cached, TTLCache
from tabulate import tabulate

# Initialize rich console for better output
console = Console()

# Setup workspace paths using pathlib
workspace_root = Path(os.path.dirname(sys.path[0])).parent.parent / 'hero-dbc'
generated_dir = workspace_root / 'scripts' / 'DBC' / 'generated'
parsed_dir = workspace_root / 'scripts' / 'DBC' / 'parsed'

os.chdir(str(workspace_root))

# Add this at the top of the file
DEPRECATED_SPELLS = {
    152173: "Deprecated Spell",
    152262: "Deprecated Spell",
    152277: "Deprecated Spell",
    188089: "Deprecated Spell",
    196924: "Deprecated Spell",
    197690: "Deprecated Spell",
    202354: "Deprecated Spell",
    202751: "Deprecated Spell",
    210802: "Deprecated Spell"
}

def safe_read_csv(file_path: Path, is_spell_file: bool = False) -> pd.DataFrame:
    """Safely read CSV file with error handling and encoding detection."""
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            # Configure dtype based on file type
            dtype = {
                'id': str,
                'desc': str,
                'row': str,
                'pet': str,
                'col': str,
                'class_id': str,
                'spec_id': str,
                'id_spell': str,
                'id_replace': str,
                'unk_1': str,
                'unk_2': str
            } if not is_spell_file else {
                'id': str,
                'name': str
            }
            
            # Read CSV with specific settings
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                on_bad_lines='skip',
                dtype=dtype
            )
            return df.fillna('')
        except UnicodeDecodeError:
            continue
        except Exception as e:
            if encoding == encodings[-1]:  # Only print error on last attempt
                console.print(f"[bold red]Error reading file {file_path} with {encoding}: {str(e)}[/bold red]")
    
    return pd.DataFrame()

@cached(cache=TTLCache(maxsize=10000, ttl=3600))
def get_spell_name(spell_id: str) -> str:
    """Get spell name with caching, handling missing entries. Uses only spell_id as cache key."""
    if not spell_id or spell_id == '0':
        return 'Unknown_0'
    
    try:
        # Check if spell is deprecated
        spell_id_int = int(spell_id)
        if spell_id_int in DEPRECATED_SPELLS:
            return DEPRECATED_SPELLS[spell_id_int]
        
        # Convert spell_df to a dictionary for faster lookups
        global spell_df
        if not hasattr(get_spell_name, 'spell_dict'):
            get_spell_name.spell_dict = spell_df.set_index('id')['name'].to_dict()
        
        return get_spell_name.spell_dict.get(str(spell_id), f'Unknown_{spell_id}')
    except Exception as e:
        console.print(f"[bold yellow]Warning: Error processing spell_id {spell_id}: {str(e)}[/bold yellow]")
        return f'Unknown_{spell_id}'

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to integer."""
    try:
        if pd.isna(value) or (isinstance(value, str) and not value.strip()):
            return default
        # Remove any non-numeric characters except decimal point
        if isinstance(value, str):
            value = ''.join(c for c in value if c.isdigit() or c == '.')
        return int(float(value))
    except (ValueError, TypeError):
        return default

def process_talent_entry(row: pd.Series) -> Optional[Dict[str, Any]]:
    """Process a single talent entry. Converts DataFrame row to dict for safer handling."""
    try:
        # Convert row to dict for safer access
        row_dict = row.to_dict()
        
        # Basic validation
        required_fields = ['id_spell', 'class_id', 'spec_id', 'row', 'col', 'id']
        if not all(field in row_dict for field in required_fields):
            reason = "Missing required fields"
            console.print(f"[yellow]Skipping entry {row.get('id', 'unknown')}: {reason}[/yellow]")
            return None

        # Get spell name
        spell_id = str(row_dict['id_spell'])
        if not spell_id or spell_id == '0':
            reason = "Invalid spell ID"
            console.print(f"[yellow]Skipping entry {row.get('id', 'unknown')}: {reason}[/yellow]")
            return None
            
        spell_name = get_spell_name(spell_id)
        
        # Create talent data
        talent_data = {
            'talentId': safe_int(row_dict['id']),
            'spellId': safe_int(spell_id),
            'spellName': spell_name
        }

        # Get classification data
        class_id = str(safe_int(row_dict['class_id']))
        spec_id = str(safe_int(row_dict['spec_id']))
        talent_row = str(safe_int(row_dict['row']))
        col = str(safe_int(row_dict['col']))

        # Skip invalid class/spec combinations
        if class_id == '0' or (spec_id == '0' and class_id == '0'):
            reason = "Invalid class/spec combination"
            console.print(f"[yellow]Skipping entry {row.get('id', 'unknown')}: {reason}[/yellow]")
            return None

        return {
            'talent_data': talent_data,
            'class_id': class_id,
            'spec_id': spec_id,
            'row': talent_row,
            'col': col,
            'spell_id': spell_id
        }

    except Exception as e:
        console.print(f"[bold red]Error processing entry {row.get('id', 'unknown')}: {str(e)}[/bold red]")
        return None

def process_talent_data(talent_df: pd.DataFrame, spell_df: pd.DataFrame) -> Tuple[Dict[str, Any], set, list, int]:
    """Process talent data into the required structure."""
    talents = {}
    missing_spells = set()
    invalid_entries = []
    processed_entries = 0

    # Process each talent entry
    for _, row in track(talent_df.iterrows(), total=len(talent_df), description="Processing talents"):
        try:
            result = process_talent_entry(row)
            if result is None:
                continue

            # Extract data from result
            talent_data = result['talent_data']
            class_id = result['class_id']
            spec_id = result['spec_id']
            talent_row = result['row']
            col = result['col']
            spell_id = result['spell_id']

            # Initialize structure if needed
            if class_id not in talents:
                talents[class_id] = {}
            if spec_id not in talents[class_id]:
                talents[class_id][spec_id] = {}
            if talent_row not in talents[class_id][spec_id]:
                talents[class_id][spec_id][talent_row] = {}

            # Store talent data
            talents[class_id][spec_id][talent_row][col] = talent_data
            processed_entries += 1

            # Track missing spells
            if 'Unknown_' in talent_data['spellName']:
                missing_spells.add(spell_id)

        except Exception as e:
            console.print(f"[bold red]Error processing entry {row.get('id', 'unknown')}: {str(e)}[/bold red]")
            invalid_entries.append((row.get('id', 'unknown'), str(e)))

    # Add detailed reporting
    if missing_spells:
        console.print("\n[bold yellow]Missing Spell Details:[/bold yellow]")
        for spell_id in sorted(missing_spells):
            entries = talent_df[talent_df['id_spell'] == spell_id]['id'].tolist()
            console.print(f"Spell ID: {spell_id} - Found in entries: {entries}")

    if invalid_entries:
        console.print("\n[bold yellow]Invalid Entry Details:[/bold yellow]")
        for entry_id, reason in sorted(invalid_entries):
            entry_data = talent_df[talent_df['id'] == entry_id].iloc[0].to_dict()
            console.print(f"Entry ID: {entry_id} - Reason: {reason}")
            console.print(f"Entry Data: {entry_data}")

    return talents, missing_spells, invalid_entries, processed_entries

# Load data using pandas
console.print("[bold blue]Loading DBC data...[/bold blue]")
talent_df = safe_read_csv(generated_dir / 'Talent.csv')
spell_df = safe_read_csv(generated_dir / 'SpellName.csv', is_spell_file=True)

if talent_df.empty or spell_df.empty:
    console.print("[bold red]Error: Failed to load required data files[/bold red]")
    sys.exit(1)

# Process talent data
console.print("[bold green]Processing talent data...[/bold green]")
talents, missing_spells, invalid_entries, processed_entries = process_talent_data(talent_df, spell_df)

# Output statistics
console.print("\n[yellow]Processing Statistics:[/yellow]")
stats = [
    ["Missing Spell Names", len(missing_spells)],
    ["Invalid Entries", len(invalid_entries)],
    ["Successfully Processed", processed_entries],
    ["Total Entries", len(talent_df)]
]
console.print(tabulate(stats, headers=['Metric', 'Count'], tablefmt='simple'))

# Write output with pretty formatting
console.print("\n[bold blue]Writing output file...[/bold blue]")
output_path = parsed_dir / 'Talent.json'
with open(output_path, 'w') as jsonFile:
    json.dump(talents, jsonFile, indent=4, sort_keys=True)

console.print(f"[bold green]Successfully generated {output_path}[/bold green]")
