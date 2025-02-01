# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
"""

import sys
import os
import csv

#List all spell that triggers an aura
#true if the aura gives 'dps' stat (simc has_stat.any_dps)
#flase if the aura gives tertiary stat or something else (simc has_stat.any)

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

# Define stat-related constants for better maintainability
AURA_TYPE = 6
DPS_SUBTYPES = {
    29,   # Attribute
    137,  # Modify Total Stat%
    193,  # Modify All Haste%
    290,  # Modify Critical Strike%
    318,  # Modify Mastery%
    471   # Modify Versatility%
}
RATING_SUBTYPE = 189
DPS_MISC_VALUES = {
    1792,        # Crit Rating
    917504,      # Haste Rating
    33554432,    # Mastery Rating
    1879048192   # Versatility Rating
}

def is_dps_stat(sub_type, misc_value):
    """Check if the spell effect modifies a DPS-related stat."""
    if sub_type in DPS_SUBTYPES:
        return True
    return sub_type == RATING_SUBTYPE and int(misc_value) in DPS_MISC_VALUES

with open(os.path.join(generatedDir, 'SpellEffect.csv')) as csvfile:
    reader = list(csv.DictReader(csvfile, escapechar='\\'))
    reader = sorted(reader, key=lambda d: int(d['id_parent']))
    
    # Pre-process to only store spells that actually modify stats
    stat_spells = {}
    for row in reader:
        spell_id = int(row['id_parent'])
        if spell_id > 0 and int(row['type']) == AURA_TYPE:
            if is_dps_stat(int(row['sub_type']), row['misc_value_1']):
                stat_spells[spell_id] = True
    
    # Write optimized output
    with open(os.path.join(addonEnumDir, 'SpellAuraStat.lua'), 'w', encoding='utf-8') as file:
        file.write('--- ============================ HEADER ============================\n')
        file.write('--- Optimized SpellAuraStat table for memory efficiency\n')
        file.write('--- Only includes spells that actually modify character stats\n')
        file.write('HeroDBC.DBC.SpellAuraStat = {\n')
        for spell_id in sorted(stat_spells.keys()):
            file.write(f'  [{spell_id}] = true,\n')
        file.write('}\n')
