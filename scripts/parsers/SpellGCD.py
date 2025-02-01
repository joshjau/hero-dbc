# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class GCDCategory(Enum):
    """Categories of GCD for better performance tracking."""
    NONE = 'none'         # Off GCD abilities
    STANDARD = 'standard' # Standard 1.5s GCD
    MODIFIED = 'modified' # Modified GCD (1.0s etc)
    CUSTOM = 'custom'     # Custom GCD duration

@dataclass
class GCDData:
    """Store GCD data with type information."""
    category: GCDCategory
    duration: int = 0  # Duration in milliseconds
    affected_by_haste: bool = False
    is_channeled: bool = False

# Constants for GCD calculations
DEFAULT_GCD = 1500  # Default GCD in milliseconds
MIN_GCD = 750      # Minimum GCD in milliseconds

# Mapping of categories to base GCDs
CATEGORY_BASE_GCD = {
    'STANDARD': DEFAULT_GCD,
    'MODIFIED': 1000,     # Some abilities use 1.0s GCD
    'CUSTOM': None        # Custom GCDs defined per spell
}

def load_gcd_data(generated_dir: Path) -> Dict[int, float]:
    """Load GCD data with fallback for missing columns."""
    gcd_data = {}
    with open(generated_dir / 'SpellMisc.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        
        # Find GCD column with fallback
        gcd_column = None
        for possible_name in ['gcd', 'global_cooldown', 'cooldown', 'gcd_cooldown']:
            if possible_name in reader.fieldnames:
                gcd_column = possible_name
                break
                
        if not gcd_column:
            print("Warning: Could not find GCD column in SpellMisc.csv, using default values")
            return gcd_data
            
        for row in reader:
            try:
                spell_id = int(row['id'])
                gcd_value = float(row[gcd_column])
                if gcd_value > 0:
                    gcd_data[spell_id] = gcd_value
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    return gcd_data

def load_spell_gcd(generated_dir: Path) -> Dict[int, GCDData]:
    """Load and validate GCD data with improved categorization."""
    gcd_data: Dict[int, GCDData] = {}
    
    with open(generated_dir / 'SpellMisc.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        # Get the actual column names from the CSV
        columns = reader.fieldnames
        
        # Find the correct GCD column name
        gcd_column = None
        for possible_name in ['gcd_cooldown', 'gcd', 'global_cooldown', 'cooldown_gcd']:
            if possible_name in columns:
                gcd_column = possible_name
                break
                
        if not gcd_column:
            print("Warning: Could not find GCD column in SpellMisc.csv")
            return gcd_data
            
        # Find the correct start recovery column name
        recovery_column = None
        for possible_name in ['start_recovery', 'recovery_time', 'recovery_start']:
            if possible_name in columns:
                recovery_column = possible_name
                break
                
        if not recovery_column:
            print("Warning: Could not find recovery time column in SpellMisc.csv")
            return gcd_data
            
        for row in reader:
            spell_id = int(row['id_parent'])
            gcd_category = int(row.get(gcd_column, 0))
            start_recovery = int(row.get(recovery_column, 0))
            
            # Skip invalid entries
            if gcd_category == 0 and start_recovery == 0:
                continue
            
            # Determine GCD category and duration
            if gcd_category == 0:
                category = GCDCategory.NONE
                duration = 0
            elif gcd_category == 1:
                category = GCDCategory.STANDARD
                duration = DEFAULT_GCD
            elif gcd_category == 2:
                category = GCDCategory.MODIFIED
                duration = CATEGORY_BASE_GCD['MODIFIED']
            else:
                category = GCDCategory.CUSTOM
                duration = start_recovery
            
            # Get flags - handle different possible column names
            flags_column = None
            for possible_name in ['flags_1', 'flags', 'spell_flags']:
                if possible_name in columns:
                    flags_column = possible_name
                    break
                    
            flags = int(row.get(flags_column, 0)) if flags_column else 0
            
            # Create GCD data entry
            gcd_data[spell_id] = GCDData(
                category=category,
                duration=duration,
                affected_by_haste=bool(flags & 0x00200000),  # Check haste flag
                is_channeled=bool(flags & 0x00000040)   # Check channeled flag
            )
    
    return gcd_data

def write_optimized_lua(output_path: Path, gcd_data: Dict[int, GCDData]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellGCD table for DPS calculations\n')
        f.write('--- Format: [spellID] = { category = "none"|"standard"|"modified"|"custom", duration = ms, haste = bool, channeled = bool }\n')
        f.write('HeroDBC.DBC.SpellGCD = {\n')
        
        # Group by GCD category for better cache locality
        by_category: Dict[GCDCategory, List[int]] = {c: [] for c in GCDCategory}
        for spell_id, data in gcd_data.items():
            by_category[data.category].append(spell_id)
        
        # Write standard GCD spells first (most common in rotations)
        for category in GCDCategory:
            if not by_category[category]:
                continue
                
            f.write(f'  -- {category.value.title()} GCD Spells\n')
            for spell_id in sorted(by_category[category]):
                data = gcd_data[spell_id]
                f.write(f'  [{spell_id}] = {{\n')
                f.write(f'    category = "{data.category.value}",\n')
                if data.duration > 0:
                    f.write(f'    duration = {data.duration},\n')
                if data.affected_by_haste:
                    f.write('    haste = true,\n')
                if data.is_channeled:
                    f.write('    channeled = true,\n')
                f.write('  },\n')
        
        f.write('}\n')

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        # Load and process data
        gcd_data = load_spell_gcd(generated_dir)
        
        # Generate optimized output
        write_optimized_lua(output_dir / 'SpellGCD.lua', gcd_data)
        print('SpellGCD data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing GCD data: {e}')
        raise

if __name__ == '__main__':
    main()
