# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>
Item Range Filter - Processes item range data for HeroDBC
"""

import sys
import os
import operator
import json
try:
    from SLPP import SLPP as lua
except ImportError:
    print("Error: SLPP module not found. Please install it using 'pip install SLPP'")
    sys.exit(1)

def process_item_range_data(ItemRangeFiltered):
    """Process the filtered item range data into a structured format"""
    ItemRange = {}
    for type, value in ItemRangeFiltered.items():
        ItemRange[type] = {}
        for reaction, value2 in value.items():
            ItemRange[type][reaction] = {}
            for key3, value3 in value2.items():
                try:
                    value3 = json.loads(value3)
                    if isinstance(value3, list):
                        ItemRangeInt = [float(val) for val in value3]
                        ItemRange[type][reaction][key3] = sorted(ItemRangeInt)
                    elif isinstance(value3, dict):
                        ItemRangeInt = {
                            float(key4): sorted(value4) 
                            for key4, value4 in value3.items()
                        }
                        ItemRangeInt = dict(sorted(ItemRangeInt.items(), key=operator.itemgetter(0)))
                        ItemRange[type][reaction][key3] = ItemRangeInt
                except (ValueError, TypeError) as e:
                    print(f"Error processing data for {type}/{reaction}/{key3}: {str(e)}")
                    continue
    return ItemRange

def write_item_range_file(file_path, ItemRange):
    """Write the processed item range data to a Lua file"""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('HeroDBC.DBC.ItemRange = {\n')
        for key, value in ItemRange.items():
            file.write(f'  {key} = {{\n')
            for key2, value2 in value.items():
                file.write(f'    {key2} = {{\n')
                for key3, value3 in value2.items():
                    if isinstance(value3, list):
                        file.write(f'      {key3} = {{\n')
                        file.writelines(f'        {float(val):g},\n' for val in value3)
                        file.write('      },\n')
                    elif isinstance(value3, dict):
                        file.write(f'      {key3} = {{\n')
                        for key4, value4 in value3.items():
                            key_str = f'[{float(key4):g}]' if isinstance(key4, (int, float)) else f'{float(key4):g}'
                            file.write(f'        {key_str} = {{\n')
                            file.writelines(f'          {float(val):g},\n' for val in value4)
                            file.write('        },\n')
                        file.write('      },\n')
                file.write('    },\n')
            file.write('  },\n')
        file.write('}\n')

def main():
    """Main processing function"""
    try:
        generatedDir = os.path.join('scripts', 'DBC', 'generated')
        addonDevDir = os.path.join('HeroDBC', 'Dev')
        addonEnumDir = os.path.join('HeroDBC', 'DBC')

        os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

        # Read and process the filtered data
        with open(os.path.join(addonDevDir, 'Filtered', 'ItemRange.lua'), 'r', encoding='utf-8') as luafile:
            data = luafile.read().replace('\n', '')
            ItemRangeFiltered = lua.decode(data)

        # Process the item range data
        ItemRange = process_item_range_data(ItemRangeFiltered)

        # Write the processed data to the output file
        write_item_range_file(os.path.join(addonEnumDir, 'ItemRange.lua'), ItemRange)

    except Exception as e:
        print(f"Error in main processing: {str(e)}")
        raise

if __name__ == '__main__':
    main()
