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

class TickType(Enum):
    """Types of periodic effects."""
    DAMAGE = 'damage'  # DoT effects
    HEAL = 'heal'     # HoT effects
    OTHER = 'other'   # Other periodic effects

@dataclass
class TickData:
    """Store tick timing data with type information."""
    amplitude: int       # Time between ticks in milliseconds
    tick_type: TickType  # Type of periodic effect
    hasted: bool = True  # Whether ticks are affected by haste

# Effect types that indicate periodic effects
PERIODIC_EFFECT_TYPES = {
    6: TickType.DAMAGE,  # Periodic damage
    7: TickType.HEAL,    # Periodic healing
    8: TickType.DAMAGE,  # Periodic leech
    23: TickType.HEAL,   # Periodic heal %
    24: TickType.DAMAGE  # Periodic damage %
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
                
                tick_type = PERIODIC_EFFECT_TYPES.get(effect_type, TickType.OTHER)
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
        effect_name = PERIODIC_EFFECT_TYPES.get(effect_type, "OTHER").name
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
        by_type: Dict[TickType, List[int]] = {t: [] for t in TickType}
        for spell_id, data in tick_data.items():
            by_type[data.tick_type].append(spell_id)
        
        # Write damage effects first (most important for DPS)
        for tick_type in TickType:
            if not by_type[tick_type]:
                continue
                
            f.write(f'  -- {tick_type.value.title()} Effects\n')
            for spell_id in sorted(by_type[tick_type]):
                data = tick_data[spell_id]
                f.write(f'  [{spell_id}] = {{\n')
                f.write(f'    amplitude = {data.amplitude},\n')
                f.write(f'    type = "{data.tick_type.value}",\n')
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
