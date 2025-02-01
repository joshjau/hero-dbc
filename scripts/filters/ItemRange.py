# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

This module processes item range data for HeroDBC, focusing on:
1. Melee range calculations
2. Spell range calculations
3. Combat range optimizations
"""

import sys
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
try:
    try:
        from slpp import slpp as lua
    except ImportError:
        from SLPP import SLPP as lua
except ImportError:
    print("Error: SLPP module not found. Please install it using 'pip install SLPP'")
    sys.exit(1)

class RangeType(Enum):
    """Types of range calculations."""
    MELEE = 'melee'      # Melee combat ranges
    RANGED = 'ranged'    # Ranged weapon ranges
    SPELL = 'spell'      # Spell cast ranges
    OTHER = 'other'      # Other range types

@dataclass
class RangeData:
    """Store range calculation data."""
    min_range: float
    max_range: float
    type: RangeType
    is_hostile: bool = True
    requires_los: bool = True

def process_item_range_data(range_data: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, List[float]]]]:
    """Process item range data with improved categorization."""
    processed_data: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    range_stats: Dict[RangeType, int] = {t: 0 for t in RangeType}
    
    for type_key, type_data in range_data.items():
        processed_data[type_key] = {}
        range_type = RangeType(type_key.lower()) if type_key.lower() in [t.value for t in RangeType] else RangeType.OTHER
        range_stats[range_type] += 1
        
        for reaction_key, reaction_data in type_data.items():
            processed_data[type_key][reaction_key] = {}
            
            for range_key, range_values in reaction_data.items():
                try:
                    # Parse and validate range values
                    if isinstance(range_values, str):
                        values = json.loads(range_values)
                    else:
                        values = range_values
                        
                    if isinstance(values, list):
                        # Convert to floats and sort
                        range_list = sorted(float(val) for val in values)
                        processed_data[type_key][reaction_key][range_key] = range_list
                    elif isinstance(values, dict):
                        # Handle nested range data
                        range_dict = {}
                        for sub_key, sub_values in values.items():
                            if isinstance(sub_values, list):
                                range_dict[float(sub_key)] = sorted(float(val) for val in sub_values)
                        processed_data[type_key][reaction_key][range_key] = dict(sorted(range_dict.items()))
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    print(f"Warning: Error processing range data for {type_key}/{reaction_key}/{range_key}: {str(e)}")
                    continue
    
    # Print range type statistics
    print("\nRange Type Statistics:")
    for range_type, count in range_stats.items():
        print(f"  {range_type.name}: {count} entries")
    
    return processed_data

def write_optimized_lua(output_path: Path, range_data: Dict[str, Dict[str, Dict[str, List[float]]]]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized ItemRange table for DPS calculations\n')
        f.write('--- Format: [type][reaction][key] = { range values... }\n')
        f.write('HeroDBC.DBC.ItemRange = {\n')
        
        # Write melee ranges first for better cache locality
        range_order = ['melee', 'ranged', 'spell', 'other']
        for range_type in range_order:
            if range_type not in range_data:
                continue
                
            f.write(f'  {range_type} = {{\n')
            for reaction, reaction_data in range_data[range_type].items():
                f.write(f'    {reaction} = {{\n')
                for key, values in reaction_data.items():
                    if isinstance(values, list):
                        f.write(f'      {key} = {{\n')
                        f.writelines(f'        {val:g},\n' for val in values)
                        f.write('      },\n')
                    elif isinstance(values, dict):
                        f.write(f'      {key} = {{\n')
                        for sub_key, sub_values in values.items():
                            f.write(f'        [{sub_key:g}] = {{\n')
                            f.writelines(f'          {val:g},\n' for val in sub_values)
                            f.write('        },\n')
                        f.write('      },\n')
                f.write('    },\n')
            f.write('  },\n')
        
        f.write('}\n')
    
    print(f"\nWrote optimized range data to {output_path}")

def main():
    """Main execution function."""
    try:
        print("Starting ItemRange processing...")
        
        # Setup paths
        root_dir = Path(__file__).parent.parent.parent
        addon_dev_dir = root_dir / 'HeroDBC' / 'Dev'
        addon_enum_dir = root_dir / 'HeroDBC' / 'DBC'
        
        # Read filtered data
        input_path = addon_dev_dir / 'Filtered' / 'ItemRange.lua'
        print(f"Reading filtered data from: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = f.read().replace('\n', '')
            range_data = lua.decode(data)
            print("Successfully decoded Lua data")
        
        # Process and optimize the data
        processed_data = process_item_range_data(range_data)
        
        # Write optimized output
        output_path = addon_enum_dir / 'ItemRange.lua'
        write_optimized_lua(output_path, processed_data)
        print("Successfully completed ItemRange processing")
        
    except Exception as e:
        print(f"Error in main processing: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
