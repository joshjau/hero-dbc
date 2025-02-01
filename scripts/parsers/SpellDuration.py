# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>
"""

import sys
import os
import csv
from typing import Dict, Tuple

generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

def load_durations() -> Dict[str, Tuple[str, str]]:
    """Load spell durations from CSV, only storing entries with positive duration."""
    durations = {}
    with open(os.path.join(generatedDir, 'SpellDuration.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            if int(row['duration_1']) > 0:
                durations[row['id']] = (row['duration_1'], row['duration_2'])
    return durations

def calculate_pandemic_duration(base_duration: int) -> int:
    """Calculate pandemic duration (30% of base duration)."""
    return int(float(base_duration) * 0.3)

def main():
    # Load duration data first
    durations = load_durations()
    
    # Process spell misc data and write output
    with open(os.path.join(generatedDir, 'SpellMisc.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        valid_spells = {}
        
        # Pre-process to collect valid spells with durations
        for row in reader:
            spell_id = int(row['id_parent'])
            duration_id = row['id_duration']
            
            if int(duration_id) > 0 and duration_id in durations:
                base_duration = int(durations[duration_id][0])
                max_duration = base_duration + calculate_pandemic_duration(base_duration)
                valid_spells[spell_id] = (base_duration, max_duration)
        
        # Write optimized output
        with open(os.path.join(addonEnumDir, 'SpellDuration.lua'), 'w', encoding='utf-8') as file:
            file.write('--- ============================ HEADER ============================\n')
            file.write('--- Optimized SpellDuration table\n')
            file.write('--- Format: [spellID] = {baseDuration, maxDuration(with pandemic)}\n')
            file.write('HeroDBC.DBC.SpellDuration = {\n')
            
            # Write sorted spells for consistent output
            for spell_id in sorted(valid_spells.keys()):
                base_duration, max_duration = valid_spells[spell_id]
                file.write(f'  [{spell_id}] = {{{base_duration}, {max_duration}}},\n')
            
            file.write('}\n')

if __name__ == '__main__':
    main()
