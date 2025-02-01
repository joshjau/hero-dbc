# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>
"""

import sys
import os
import csv
from typing import Dict, Tuple, List
from dataclasses import dataclass
from pathlib import Path

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

@dataclass
class RangeData:
    """Store range data with type information."""
    min_range: int
    max_range: int
    is_melee: bool

def process_spell_ranges(generated_dir: Path) -> Dict[int, Tuple[float, float]]:
    """Process spell ranges and identify special cases."""
    special_cases = {}
    with open(generated_dir / 'SpellRange.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        
        # Find range columns with fallback
        min_range_col = None
        max_range_col = None
        for possible_min in ['min_range', 'min_range_1', 'range_min']:
            if possible_min in reader.fieldnames:
                min_range_col = possible_min
                break
                
        for possible_max in ['max_range', 'max_range_1', 'range_max']:
            if possible_max in reader.fieldnames:
                max_range_col = possible_max
                break
                
        if not min_range_col or not max_range_col:
            print("Warning: Could not find range columns in SpellRange.csv")
            return special_cases
            
        for row in reader:
            try:
                spell_id = int(row['id'])
                min_range = float(row[min_range_col])
                max_range = float(row[max_range_col])
                
                # Identify special cases
                if max_range > 5 or min_range != 0:  # Non-standard range
                    special_cases[spell_id] = (min_range, max_range)
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    return special_cases

def get_spell_range_mappings(ranges: Dict[str, RangeData]) -> Dict[int, RangeData]:
    """Get spell to range mappings from SpellMisc.csv."""
    spell_ranges = {}
    with open(os.path.join(generatedDir, 'SpellMisc.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            spell_id = int(row['id_parent'])
            range_id = row['id_range']
            
            # Special case handling for spells with unique range mechanics
            if spell_id in [100, 200]:  # Example spell IDs
                spell_ranges[spell_id] = RangeData(
                    min_range=0,
                    max_range=8,
                    is_melee=False
                )
                continue
                
            # Only process spells with valid ranges
            if range_id in ranges:
                spell_ranges[spell_id] = ranges[range_id]
    return spell_ranges

def write_optimized_lua(output_path: Path, special_cases: Dict[int, Tuple[float, float]]):
    """Write optimized Lua output with special cases."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellMeleeRange table\n')
        f.write('--- Format: [SpellID] = { [1] = IsMelee, [2] = MinRange, [3] = MaxRange }\n')
        f.write('HeroDBC.DBC.SpellMeleeRange = {\n')
        
        # Write special cases
        for spell_id, (min_range, max_range) in sorted(special_cases.items()):
            f.write(f'  [{spell_id}] = {{{min_range}, {max_range}}}, -- Special case\n')
        
        f.write('}\n')

def main():
    # Load and process data
    ranges = process_spell_ranges(Path(generatedDir))
    
    # Generate output
    write_optimized_lua(Path(addonEnumDir) / 'SpellMeleeRange.lua', ranges)

if __name__ == '__main__':
    main()
