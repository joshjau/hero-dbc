# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>
"""

import sys
import os
import csv
from typing import Dict, List, Tuple, Union
from dataclasses import dataclass

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonDevDir = os.path.join('HeroDBC', 'Dev')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

@dataclass
class RangeData:
    """Store range data with type information."""
    max_range: float
    flag: int

def load_item_spells() -> Dict[str, str]:
    """Load spell to item mappings from ItemEffect.csv."""
    items = {}
    with open(os.path.join(generatedDir, 'ItemEffect.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            if row['id_spell'] and row['id']:  # Only store valid mappings
                items[row['id_spell']] = row['id']
    return items

def process_spell_ranges() -> Dict[str, RangeData]:
    """Process and validate spell ranges from SpellRange.csv."""
    ranges = {}
    with open(os.path.join(generatedDir, 'SpellRange.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            # Process hostile ranges
            min_range_1 = float(row['min_range_1'])
            max_range_1 = float(row['max_range_1'])
            if min_range_1 == 0 and 5 <= max_range_1 <= 100:
                ranges[row['id']] = RangeData(max_range_1, int(row['flag']))
            
            # Process friendly ranges
            min_range_2 = float(row['min_range_2'])
            max_range_2 = float(row['max_range_2'])
            if min_range_2 == 0 and 5 <= max_range_2 <= 100:
                ranges[row['id']] = RangeData(max_range_2, int(row['flag']))
    return ranges

def build_item_range_data(items: Dict[str, str], ranges: Dict[str, RangeData]) -> Dict[str, Dict[float, List[int]]]:
    """Build the item range data structure."""
    item_range = {
        'Melee': {},
        'Ranged': {}
    }
    
    with open(os.path.join(generatedDir, 'SpellMisc.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            id_misc = row['id_parent']
            if id_misc in items and row['id_range'] in ranges:
                range_data = ranges[row['id_range']]
                target_dict = item_range['Melee'] if range_data.flag == 1 else item_range['Ranged']
                
                if range_data.max_range not in target_dict:
                    target_dict[range_data.max_range] = []
                
                target_dict[range_data.max_range].append(int(items[id_misc]))
    
    return item_range

def write_lua_output(item_range: Dict[str, Dict[float, List[int]]]):
    """Write the optimized Lua output file."""
    with open(os.path.join(addonDevDir, 'Unfiltered', 'ItemRange.lua'), 'w', encoding='utf-8') as file:
        file.write('--- ============================ HEADER ============================\n')
        file.write('--- Optimized ItemRange table\n')
        file.write('--- Format: { [Type] = { [Range] = { [1] = ItemID, [2] = ItemId, ... } } }\n')
        file.write('HeroDBC.DBC.ItemRangeUnfiltered = {\n')
        
        for range_type, ranges in item_range.items():
            file.write(f'  {range_type} = {{\n')
            
            # Sort ranges for consistent output
            for range_value, items in sorted(ranges.items()):
                file.write(f'    [{range_value:g}] = {{\n')
                for item_id in sorted(items):
                    file.write(f'      {item_id},\n')
                file.write('    },\n')
            
            file.write('  },\n')
        
        file.write('}\n')

def main():
    # Load and process data
    items = load_item_spells()
    ranges = process_spell_ranges()
    item_range = build_item_range_data(items, ranges)
    
    # Generate output
    write_lua_output(item_range)

if __name__ == '__main__':
    main()
