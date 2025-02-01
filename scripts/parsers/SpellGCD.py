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

def load_spell_gcd(generated_dir: Path) -> Dict[int, GCDData]:
    """Load and validate GCD data with improved categorization."""
    gcd_data: Dict[int, GCDData] = {}
    
    with open(generated_dir / 'SpellMisc.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        for row in reader:
            spell_id = int(row['id_parent'])
            gcd_category = int(row['gcd_cooldown'])
            start_recovery = int(row['start_recovery'])
            
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
            
            # Create GCD data entry
            gcd_data[spell_id] = GCDData(
                category=category,
                duration=duration,
                affected_by_haste=bool(int(row['flags_1']) & 0x00200000),  # Check haste flag
                is_channeled=bool(int(row['flags_1']) & 0x00000040)   # Check channeled flag
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
