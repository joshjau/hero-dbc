# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class DurationType(Enum):
    """Types of spell durations for better categorization."""
    DAMAGE = 'damage'      # DoTs and damage buffs
    COOLDOWN = 'cooldown'  # Ability cooldowns
    UTILITY = 'utility'    # Non-damage effects

@dataclass
class DurationData:
    """Store duration data with type information."""
    base_duration: int  # Duration in milliseconds
    duration_type: DurationType
    max_stacks: int = 1
    has_haste: bool = False
    has_mastery: bool = False

# Mapping of effect types to duration categories
EFFECT_TO_DURATION_TYPE = {
    # Damage effects
    2: DurationType.DAMAGE,   # Apply Aura: Mod Damage Done (Periodic)
    3: DurationType.DAMAGE,   # Apply Aura: Mod Periodic Damage
    53: DurationType.DAMAGE,  # Apply Aura: Mod Critical Damage
    # Cooldown effects
    107: DurationType.COOLDOWN,  # Apply Aura: Add Flat Modifier
    189: DurationType.COOLDOWN,  # Apply Aura: Mod Cooldown
    # Utility effects
    6: DurationType.UTILITY,   # Apply Aura: Mod Stat
    12: DurationType.UTILITY,  # Apply Aura: Mod Speed
}

def load_spell_durations(generated_dir: Path) -> Dict[int, DurationData]:
    """Load and validate spell durations with improved categorization."""
    duration_data: Dict[int, DurationData] = {}
    
    # First pass: Load base durations
    with open(generated_dir / 'SpellDuration.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        for row in reader:
            spell_id = int(row['id'])
            base_duration = int(row['duration_1'])
            
            if base_duration <= 0:
                continue
                
            duration_data[spell_id] = DurationData(
                base_duration=base_duration,
                duration_type=DurationType.DAMAGE,  # Default to DAMAGE, will be refined later
                max_stacks=1
            )
    
    # Second pass: Refine duration types and add modifiers
    with open(generated_dir / 'SpellEffect.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        for row in reader:
            spell_id = int(row['id_parent'])
            if spell_id not in duration_data:
                continue
                
            effect_type = int(row['type'])
            if effect_type in EFFECT_TO_DURATION_TYPE:
                duration_data[spell_id].duration_type = EFFECT_TO_DURATION_TYPE[effect_type]
            
            # Check for haste/mastery scaling
            aura_type = int(row['effect_aura'] if 'effect_aura' in row else row.get('aura_type', 0))
            if aura_type in (319, 320):  # Haste-affected auras
                duration_data[spell_id].has_haste = True
            elif aura_type in (98, 99):  # Mastery-affected auras
                duration_data[spell_id].has_mastery = True
            
            # Update max stacks if applicable
            max_stacks = int(row.get('aura_points', 0))
            if max_stacks > duration_data[spell_id].max_stacks:
                duration_data[spell_id].max_stacks = max_stacks
    
    return duration_data

def write_optimized_lua(output_path: Path, duration_data: Dict[int, DurationData]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellDuration table for DPS calculations\n')
        f.write('--- Format: [spellID] = { duration = ms, type = "damage"|"cooldown"|"utility", stacks = n, haste = bool, mastery = bool }\n')
        f.write('HeroDBC.DBC.SpellDuration = {\n')
        
        # Group by duration type for better cache locality
        by_type: Dict[DurationType, List[int]] = {t: [] for t in DurationType}
        for spell_id, data in duration_data.items():
            by_type[data.duration_type].append(spell_id)
        
        # Write damage durations first (most important for DPS)
        for duration_type in DurationType:
            if not by_type[duration_type]:
                continue
                
            f.write(f'  -- {duration_type.value.title()} Effects\n')
            for spell_id in sorted(by_type[duration_type]):
                data = duration_data[spell_id]
                f.write(f'  [{spell_id}] = {{\n')
                f.write(f'    duration = {data.base_duration},\n')
                f.write(f'    type = "{data.duration_type.value}",\n')
                if data.max_stacks > 1:
                    f.write(f'    stacks = {data.max_stacks},\n')
                if data.has_haste:
                    f.write('    haste = true,\n')
                if data.has_mastery:
                    f.write('    mastery = true,\n')
                f.write('  },\n')
        
        f.write('}\n')

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        # Load and process data
        duration_data = load_spell_durations(generated_dir)
        
        # Generate optimized output
        write_optimized_lua(output_dir / 'SpellDuration.lua', duration_data)
        print('SpellDuration data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing duration data: {e}')
        raise

if __name__ == '__main__':
    main()
