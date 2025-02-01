# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>
"""

import sys
import os
import csv
from typing import Dict

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

def process_gcd_data() -> Dict[int, int]:
    """Process GCD data and return only non-zero GCD values."""
    gcd_data = {}
    with open(os.path.join(generatedDir, 'SpellCooldowns.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            spell_id = int(row['id_parent'])
            gcd = int(row['gcd_cooldown'])
            if spell_id > 0 and gcd > 0:  # Only store spells with actual GCD values
                gcd_data[spell_id] = gcd
    return gcd_data

def main():
    # Get GCD data
    gcd_data = process_gcd_data()
    
    # Write optimized output
    with open(os.path.join(addonEnumDir, 'SpellGCD.lua'), 'w', encoding='utf-8') as file:
        file.write('--- ============================ HEADER ============================\n')
        file.write('--- Optimized SpellGCD table - Only includes spells with non-zero GCD\n')
        file.write('--- Format: [spellID] = gcdDuration (in milliseconds)\n')
        file.write('HeroDBC.DBC.SpellGCD = {\n')
        
        # Write sorted spells for consistent output
        for spell_id in sorted(gcd_data.keys()):
            file.write(f'  [{spell_id}] = {gcd_data[spell_id]},\n')
        
        file.write('}\n')

if __name__ == '__main__':
    main()
