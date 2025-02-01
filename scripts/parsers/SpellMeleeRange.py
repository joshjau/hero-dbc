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

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

@dataclass
class RangeData:
    """Store range data with type information."""
    min_range: int
    max_range: int
    is_melee: bool

def process_spell_ranges() -> Dict[str, RangeData]:
    """Process and validate spell ranges from SpellRange.csv.
    Only considers hostile ranges (_1) and validates range values."""
    ranges = {}
    with open(os.path.join(generatedDir, 'SpellRange.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            min_range = float(row['min_range_1'])
            max_range = float(row['max_range_1'])
            
            # Only process valid ranges (max > 0 and <= 100)
            if max_range > 0 and max_range <= 100:
                ranges[row['id']] = RangeData(
                    min_range=int(min_range),
                    max_range=int(max_range),
                    is_melee=(int(row['flag']) == 1)
                )
    return ranges

def get_spell_range_mappings(ranges: Dict[str, RangeData]) -> Dict[int, RangeData]:
    """Get spell to range mappings from SpellMisc.csv."""
    spell_ranges = {}
    with open(os.path.join(generatedDir, 'SpellMisc.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            spell_id = int(row['id_parent'])
            range_id = row['id_range']
            
            # Only process spells with valid ranges
            if range_id in ranges:
                spell_ranges[spell_id] = ranges[range_id]
    return spell_ranges

def write_lua_output(spell_ranges: Dict[int, RangeData]):
    """Write the optimized Lua output file."""
    with open(os.path.join(addonEnumDir, 'SpellMeleeRange.lua'), 'w', encoding='utf-8') as file:
        file.write('--- ============================ HEADER ============================\n')
        file.write('--- Optimized SpellMeleeRange table\n')
        file.write('--- Format: [SpellID] = { [1] = IsMelee, [2] = MinRange, [3] = MaxRange }\n')
        file.write('HeroDBC.DBC.SpellMeleeRange = {\n')
        
        # Write sorted spells for consistent output
        for spell_id in sorted(spell_ranges.keys()):
            range_data = spell_ranges[spell_id]
            file.write(f'  [{spell_id}] = {{ {str(range_data.is_melee).lower()}, {range_data.min_range}, {range_data.max_range} }},\n')
        
        file.write('}\n')

def main():
    # Load and process data
    ranges = process_spell_ranges()
    spell_ranges = get_spell_range_mappings(ranges)
    
    # Generate output
    write_lua_output(spell_ranges)

if __name__ == '__main__':
    main()
