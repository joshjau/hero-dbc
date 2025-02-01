# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

Column mappings for CSV files:
SpellEffect.csv:
    - id_parent: Parent spell ID
    - type: Effect type
    - aura: Aura type
    - misc_value_1: Affected stat ID
    - base_value: Stat modification value
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class StatType(Enum):
    """Types of stats that can be modified."""
    STRENGTH = 4         # Base and bonus strength
    AGILITY = 3         # Base and bonus agility
    STAMINA = 7         # Base and bonus stamina
    INTELLECT = 5       # Base and bonus intellect
    CRIT = 32           # Critical strike rating
    HASTE = 36          # Haste rating
    MASTERY = 49        # Mastery rating
    VERSATILITY = 40    # Versatility rating
    ATTACK_POWER = 99   # Attack power
    SPELL_POWER = 85    # Spell power
    OTHER = 999         # Other stats

@dataclass
class StatModification:
    """Store stat modification data."""
    stat_type: StatType  # Type of stat being modified
    value: int          # Modification value
    is_percent: bool    # Whether the modification is a percentage
    is_primary: bool    # Whether it's a primary stat

# Aura types that indicate stat modifications
STAT_AURA_TYPES = {
    29: True,   # MOD_STAT
    137: True,  # MOD_TOTAL_STAT_PERCENTAGE
    189: False, # MOD_RATING
}

# Primary stats for better categorization
PRIMARY_STATS = {
    StatType.STRENGTH,
    StatType.AGILITY,
    StatType.INTELLECT,
    StatType.STAMINA
}

def process_stat_mods(generated_dir: Path) -> Dict[int, List[StatModification]]:
    """Process spell stat modifications with improved categorization."""
    stat_data: Dict[int, List[StatModification]] = {}
    stat_type_counts: Dict[int, int] = {}  # Track frequency of stat types
    
    with open(generated_dir / 'SpellEffect.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        print(f"Available columns in SpellEffect.csv: {', '.join(reader.fieldnames)}")
        
        for row in reader:
            try:
                spell_id = int(row['id_parent'])
                aura_type = int(row['aura'])
                
                # Skip non-stat modifications
                if aura_type not in STAT_AURA_TYPES:
                    continue
                
                effect_type = int(row['type'])
                if effect_type != 6:  # SPELL_EFFECT_APPLY_AURA
                    continue
                
                stat_id = int(row['misc_value_1'])
                stat_type_counts[stat_id] = stat_type_counts.get(stat_id, 0) + 1
                
                try:
                    stat_type = StatType(stat_id)
                except ValueError:
                    if stat_id > 0:
                        print(f"Warning: Unknown stat type {stat_id} for spell {spell_id}")
                    continue
                
                # Initialize list if needed
                if spell_id not in stat_data:
                    stat_data[spell_id] = []
                
                value = int(row['base_value'])
                is_percent = STAT_AURA_TYPES[aura_type]  # True for percentage mods
                
                stat_data[spell_id].append(StatModification(
                    stat_type=stat_type,
                    value=value,
                    is_percent=is_percent,
                    is_primary=stat_type in PRIMARY_STATS
                ))
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    # Print stat type statistics
    print("\nStat Type Statistics:")
    for stat_id, count in sorted(stat_type_counts.items()):
        try:
            stat_name = StatType(stat_id).name
        except ValueError:
            stat_name = "UNKNOWN"
        print(f"  {stat_name} (ID {stat_id}): {count} occurrences")
    
    print(f"\nProcessed {len(stat_data)} spells with stat modifications")
    return stat_data

def write_optimized_lua(output_path: Path, stat_data: Dict[int, List[StatModification]]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellAuraStat table for DPS calculations\n')
        f.write('--- Format: [spellID] = { { stat = "str"|"agi"|etc, value = n, percent = bool, primary = bool }, ... }\n')
        f.write('HeroDBC.DBC.SpellAuraStat = {\n')
        
        # Group spells by primary stat presence for better cache locality
        primary_spells = []
        secondary_spells = []
        for spell_id, mods in stat_data.items():
            if any(mod.is_primary for mod in mods):
                primary_spells.append(spell_id)
            else:
                secondary_spells.append(spell_id)
        
        # Write primary stat modifications first (most important)
        if primary_spells:
            f.write('  -- Primary Stat Modifications\n')
            for spell_id in sorted(primary_spells):
                write_spell_mods(f, spell_id, stat_data[spell_id])
        
        if secondary_spells:
            f.write('  -- Secondary Stat Modifications\n')
            for spell_id in sorted(secondary_spells):
                write_spell_mods(f, spell_id, stat_data[spell_id])
        
        f.write('}\n')
    
    print(f"\nWrote optimized stat modification data to {output_path}")

def write_spell_mods(f, spell_id: int, mods: List[StatModification]):
    """Write spell modifications in an optimized format."""
    f.write(f'  [{spell_id}] = {{\n')
    for mod in sorted(mods, key=lambda m: (not m.is_primary, m.stat_type.name)):
        stat_name = mod.stat_type.name.lower()
        f.write('    {\n')
        f.write(f'      stat = "{stat_name}",\n')
        f.write(f'      value = {mod.value},\n')
        if mod.is_percent:
            f.write('      percent = true,\n')
        if mod.is_primary:
            f.write('      primary = true,\n')
        f.write('    },\n')
    f.write('  },\n')

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        print("Starting stat modification data processing...")
        
        # Process and write data
        stat_data = process_stat_mods(generated_dir)
        write_optimized_lua(output_dir / 'SpellAuraStat.lua', stat_data)
        print('SpellAuraStat data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing stat modification data: {e}')
        raise

if __name__ == '__main__':
    main()
