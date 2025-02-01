# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

Column mappings for CSV files:
SpellEffect.csv:
    - id_parent: Parent spell ID
    - amplitude: Time between ticks in milliseconds
    - id_mechanic: Mechanic ID (15 = stun)
    - type: Effect type (6 = periodic damage, 7 = periodic heal)
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

@dataclass
class TickData:
    """Store tick timing data with type information."""
    amplitude: int       # Time between ticks in milliseconds
    tick_type: str       # Type of periodic effect (string)
    hasted: bool = True  # Whether ticks are affected by haste

# Move PERIODIC_EFFECT_TYPES closer to where it's used
PERIODIC_EFFECT_TYPES = {
    6: "DAMAGE",
    7: "HEAL",
    8: "APPLY_AURA",
    9: "ENERGIZE",
    10: "WEAPON_DAMAGE",
    11: "SCRIPT_EFFECT",
    12: "INTERRUPT_CAST",
    13: "DUMMY",
    14: "SCRIPT_EFFECT",
    15: "ATTACK_ME",
    16: "DURABILITY_DAMAGE",
    17: "SPAWN",
    18: "SPELL_CAST",
    19: "LEECH",
    20: "MANA_LEECH",
    21: "HEALTH_LEECH",
    22: "HOLY_POWER",
    23: "ENERGIZE_PCT",
    24: "DAMAGE_PCT",
    25: "HEAL_PCT",
    26: "ENERGIZE_PCT",
    27: "DAMAGE_PCT",
    28: "HEAL_PCT",
    29: "SCRIPT_EFFECT",
    30: "SCRIPT_EFFECT",
    31: "SCRIPT_EFFECT",
    32: "SCRIPT_EFFECT",
    33: "SCRIPT_EFFECT",
    34: "SCRIPT_EFFECT",
    35: "SCRIPT_EFFECT",
    36: "SCRIPT_EFFECT",
    37: "SCRIPT_EFFECT",
    38: "SCRIPT_EFFECT",
    39: "SCRIPT_EFFECT",
    40: "SCRIPT_EFFECT",
    41: "SCRIPT_EFFECT",
    42: "SCRIPT_EFFECT",
    43: "SCRIPT_EFFECT",
    44: "SCRIPT_EFFECT",
    45: "SCRIPT_EFFECT",
    46: "SCRIPT_EFFECT",
    47: "SCRIPT_EFFECT",
    48: "SCRIPT_EFFECT",
    49: "SCRIPT_EFFECT",
    50: "SCRIPT_EFFECT",
    51: "SCRIPT_EFFECT",
    52: "SCRIPT_EFFECT",
    53: "SCRIPT_EFFECT",
    54: "SCRIPT_EFFECT",
    55: "SCRIPT_EFFECT",
    56: "SCRIPT_EFFECT",
    57: "SCRIPT_EFFECT",
    58: "SCRIPT_EFFECT",
    59: "SCRIPT_EFFECT",
    60: "SCRIPT_EFFECT",
    61: "SCRIPT_EFFECT",
    62: "SCRIPT_EFFECT",
    63: "SCRIPT_EFFECT",
    64: "SCRIPT_EFFECT",
    65: "SCRIPT_EFFECT",
    66: "SCRIPT_EFFECT",
    67: "SCRIPT_EFFECT",
    68: "SCRIPT_EFFECT",
    69: "SCRIPT_EFFECT",
    70: "SCRIPT_EFFECT",
    71: "SCRIPT_EFFECT",
    72: "SCRIPT_EFFECT",
    73: "SCRIPT_EFFECT",
    74: "SCRIPT_EFFECT",
    75: "SCRIPT_EFFECT",
    76: "SCRIPT_EFFECT",
    77: "SCRIPT_EFFECT",
    78: "SCRIPT_EFFECT",
    79: "SCRIPT_EFFECT",
    80: "SCRIPT_EFFECT",
    81: "SCRIPT_EFFECT",
    82: "SCRIPT_EFFECT",
    83: "SCRIPT_EFFECT",
    84: "SCRIPT_EFFECT",
    85: "SCRIPT_EFFECT",
    86: "SCRIPT_EFFECT",
    87: "SCRIPT_EFFECT",
    88: "SCRIPT_EFFECT",
    89: "SCRIPT_EFFECT",
    90: "SCRIPT_EFFECT",
    91: "SCRIPT_EFFECT",
    92: "SCRIPT_EFFECT",
    93: "SCRIPT_EFFECT",
    94: "SCRIPT_EFFECT",
    95: "SCRIPT_EFFECT",
    96: "SCRIPT_EFFECT",
    97: "SCRIPT_EFFECT",
    98: "SCRIPT_EFFECT",
    99: "SCRIPT_EFFECT",
    100: "SCRIPT_EFFECT"
}

def process_tick_data(generated_dir: Path) -> Dict[int, TickData]:
    """Process spell tick timing data with improved categorization."""
    tick_data: Dict[int, TickData] = {}
    effect_type_counts: Dict[int, int] = {}  # Track frequency of effect types
    
    with open(generated_dir / 'SpellEffect.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        print(f"Available columns in SpellEffect.csv: {', '.join(reader.fieldnames)}")
        
        for row in reader:
            try:
                spell_id = int(row['id_parent'])
                amplitude = int(row['amplitude'])
                effect_type = int(row['type'])
                mechanic = int(row.get('id_mechanic', 0))
                
                # Skip non-periodic effects
                if amplitude == 0:
                    continue
                    
                # Track effect type frequency
                effect_type_counts[effect_type] = effect_type_counts.get(effect_type, 0) + 1
                
                # Only store first periodic effect per spell
                if spell_id in tick_data:
                    continue
                
                tick_type = PERIODIC_EFFECT_TYPES.get(effect_type, "OTHER")
                tick_data[spell_id] = TickData(
                    amplitude=amplitude,
                    tick_type=tick_type,
                    hasted=(mechanic != 15)  # Stun effects aren't hasted
                )
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    # Print effect type statistics
    print("\nEffect Type Statistics:")
    for effect_type, count in sorted(effect_type_counts.items()):
        effect_name = PERIODIC_EFFECT_TYPES.get(effect_type, "OTHER")
        print(f"  {effect_name} (Type {effect_type}): {count} occurrences")
    
    print(f"\nProcessed {len(tick_data)} spells with periodic effects")
    return tick_data

def write_optimized_lua(output_path: Path, tick_data: Dict[int, TickData]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellTickTime table for DPS calculations\n')
        f.write('--- Format: [spellID] = { amplitude = ms, type = "damage"|"heal"|"other", hasted = bool }\n')
        f.write('HeroDBC.DBC.SpellTickTime = {\n')
        
        # Group by tick type for better cache locality
        by_type: Dict[str, List[int]] = {
            "DAMAGE": [],
            "HEAL": [],
            "DAMAGE_PCT": [],
            "HEAL_PCT": [],
            "ENERGIZE_PCT": [],
            "OTHER": []
        }
        
        for spell_id, data in tick_data.items():
            # Map all damage/heal variants to their base types
            if data.tick_type.endswith("_PCT"):
                base_type = data.tick_type.split("_")[0]
                by_type[base_type].append(spell_id)
            else:
                by_type.get(data.tick_type, by_type["OTHER"]).append(spell_id)
        
        # Write damage effects first (most important for DPS)
        for tick_type, spell_ids in by_type.items():
            if not spell_ids:
                continue
                
            f.write(f'  -- {tick_type.title()} Effects\n')
            for spell_id in sorted(spell_ids):
                data = tick_data[spell_id]
                f.write(f'  [{spell_id}] = {{\n')
                f.write(f'    amplitude = {data.amplitude},\n')
                f.write(f'    type = "{data.tick_type}",\n')
                if not data.hasted:  # Only write hasted if false to save space
                    f.write('    hasted = false,\n')
                f.write('  },\n')
        
        f.write('}\n')
    
    print(f"\nWrote optimized tick timing data to {output_path}")

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        print("Starting spell tick timing data processing...")
        
        # Process and write data
        tick_data = process_tick_data(generated_dir)
        write_optimized_lua(output_dir / 'SpellTickTime.lua', tick_data)
        print('SpellTickTime data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing tick timing data: {e}')
        raise

if __name__ == '__main__':
    main()
