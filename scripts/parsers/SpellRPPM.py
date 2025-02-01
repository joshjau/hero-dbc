# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
"""

import sys
import os
import csv
from typing import Dict, Union, Any
from dataclasses import dataclass

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

# Constants for RPPM types and mappings
RPPM_TYPES = {
    1: 'HASTE',
    2: 'CRIT',
    3: 'CLASS',
    4: 'SPEC',
    5: 'RACE'
}

CLASS_MASKS = {
    i: 1 << (i-1) for i in range(1, 13)
}

RACE_NAMES = {
    1: 'Human',
    2: 'Orc',
    3: 'Dwarf',
    4: 'NightElf',
    5: 'Scourge',
    6: 'Tauren',
    7: 'Gnome',
    8: 'Troll',
    9: 'Goblin',
    10: 'BloodElf',
    11: 'Draenei',
    24: 'Pandaren',
    25: 'Pandaren',
    26: 'Pandaren',
    27: 'Nightborne',
    28: 'HighmountainTauren',
    29: 'VoidElf',
    30: 'LightforgedDraenei'
}

def load_base_ppm() -> Dict[int, float]:
    """Load base PPM values from SpellProcsPerMinute.csv."""
    base_ppm = {}
    with open(os.path.join(generatedDir, 'SpellProcsPerMinute.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            ppm_id = int(row['id'])
            ppm_value = float(row['ppm'])
            if ppm_value > 0:  # Only store non-zero PPM values
                base_ppm[ppm_id] = ppm_value
    return base_ppm

def process_ppm_modifiers(base_ppm: Dict[int, float]) -> Dict[int, Dict[int, Any]]:
    """Process PPM modifiers from SpellProcsPerMinuteMod.csv."""
    mod_ppm = {}
    with open(os.path.join(generatedDir, 'SpellProcsPerMinuteMod.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            parent_id = int(row['id_parent'])
            mod_type = int(row['unk_1'])
            
            if mod_type not in RPPM_TYPES:
                continue
                
            if parent_id not in mod_ppm:
                mod_ppm[parent_id] = {}
                
            rppm_type = RPPM_TYPES[mod_type]
            
            # Handle different modifier types
            if rppm_type in ('HASTE', 'CRIT'):
                mod_ppm[parent_id][mod_type] = True
            elif rppm_type == 'CLASS':
                if mod_type not in mod_ppm[parent_id]:
                    mod_ppm[parent_id][mod_type] = {}
                    
                class_mask = int(row['id_chr_spec'])
                for class_id, mask in CLASS_MASKS.items():
                    if class_mask & mask:
                        mod_ppm[parent_id][mod_type][class_id] = base_ppm[parent_id] * (1.0 + float(row['coefficient']))
            elif rppm_type in ('SPEC', 'RACE'):
                if mod_type not in mod_ppm[parent_id]:
                    mod_ppm[parent_id][mod_type] = {}
                spec_id = int(row['id_chr_spec'])
                mod_ppm[parent_id][mod_type][spec_id] = base_ppm[parent_id] * (1.0 + float(row['coefficient']))
                
    return mod_ppm

def get_spell_ppm_mappings() -> Dict[int, int]:
    """Get spell to PPM ID mappings from SpellAuraOptions.csv."""
    ppm_mappings = {}
    with open(os.path.join(generatedDir, 'SpellAuraOptions.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            spell_id = int(row['id_parent'])
            ppm_id = int(row['id_ppm'])
            if ppm_id > 0:  # Only store spells with PPM
                ppm_mappings[spell_id] = ppm_id
    return ppm_mappings

def write_lua_output(ppm_mappings: Dict[int, int], base_ppm: Dict[int, float], mod_ppm: Dict[int, Dict[int, Any]]):
    """Write the optimized Lua output file."""
    with open(os.path.join(addonEnumDir, 'SpellRPPM.lua'), 'w', encoding='utf-8') as file:
        file.write('--- ============================ HEADER ============================\n')
        file.write('--- Optimized SpellRPPM table\n')
        file.write('--- [spellID] = { [0] = basePPM, [modType] = modifierData }\n')
        file.write('HeroDBC.DBC.SpellRPPM = {\n')
        
        for spell_id in sorted(ppm_mappings.keys()):
            ppm_id = ppm_mappings[spell_id]
            if ppm_id not in base_ppm:
                continue
                
            file.write(f'  [{spell_id}] = {{\n')
            file.write(f'    [0] = {base_ppm[ppm_id]},\n')
            
            if ppm_id in mod_ppm:
                for mod_type, mod_data in mod_ppm[ppm_id].items():
                    if isinstance(mod_data, bool):
                        file.write(f'    [{mod_type}] = {str(mod_data).lower()},\n')
                    elif isinstance(mod_data, dict):
                        file.write(f'    [{mod_type}] = {{\n')
                        for sub_id, value in sorted(mod_data.items()):
                            file.write(f'      [{sub_id}] = {value},\n')
                        file.write('    },\n')
            
            file.write('  },\n')
        
        file.write('}\n')

def main():
    # Load and process data
    base_ppm = load_base_ppm()
    mod_ppm = process_ppm_modifiers(base_ppm)
    ppm_mappings = get_spell_ppm_mappings()
    
    # Generate output
    write_lua_output(ppm_mappings, base_ppm, mod_ppm)

if __name__ == '__main__':
    main()
