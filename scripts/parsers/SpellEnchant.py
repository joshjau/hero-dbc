# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

Column mappings for CSV files:
SpellItemEnchantment.csv:
    - id: Enchantment ID
    - type_1/2/3: Effect types (1=stat, 4=proc)
    - id_property_1/2/3: Property IDs
    - value_1/2/3: Effect values
    - id_spell: Proc spell ID
    - scaling_class: Scaling type
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class EnchantType(Enum):
    """Types of enchantment effects."""
    STAT = 1       # Direct stat bonus
    PROC = 4       # Proc effect
    SCALING = 5    # Level-scaled effect
    OTHER = 999    # Other effect types

@dataclass
class EnchantEffect:
    """Store enchantment effect data."""
    effect_type: EnchantType
    property_id: int
    value: int
    spell_id: int = 0
    scaling_type: int = 0

@dataclass
class EnchantData:
    """Store complete enchantment data."""
    effects: List[EnchantEffect]
    is_dps: bool = False  # Whether it affects DPS

# Stats that affect DPS
DPS_PROPERTIES = {
    1: True,   # Agility
    4: True,   # Strength
    5: True,   # Intellect
    32: True,  # Crit Rating
    36: True,  # Haste Rating
    49: True,  # Mastery Rating
    40: True,  # Versatility Rating
    99: True,  # Attack Power
    85: True   # Spell Power
}

def process_enchants(generated_dir: Path) -> Dict[int, EnchantData]:
    """Process enchantment data with improved categorization."""
    enchant_data: Dict[int, EnchantData] = {}
    effect_type_counts: Dict[int, int] = {}  # Track frequency of effect types
    
    with open(generated_dir / 'SpellItemEnchantment.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        print(f"Available columns in SpellItemEnchantment.csv: {', '.join(reader.fieldnames)}")
        
        for row in reader:
            try:
                enchant_id = int(row['id'])
                effects = []
                is_dps = False
                
                # Process each effect slot
                for i in range(1, 4):
                    effect_type = int(row[f'type_{i}'])
                    if effect_type == 0:
                        continue
                        
                    effect_type_counts[effect_type] = effect_type_counts.get(effect_type, 0) + 1
                    
                    try:
                        enchant_type = EnchantType(effect_type)
                    except ValueError:
                        print(f"Warning: Unknown effect type {effect_type} for enchant {enchant_id}")
                        enchant_type = EnchantType.OTHER
                    
                    property_id = int(row[f'id_property_{i}'])
                    value = int(row[f'value_{i}'])
                    spell_id = int(row.get('id_spell', 0))
                    scaling_type = int(row.get('scaling_class', 0))
                    
                    # Check if this is a DPS-affecting enchant
                    if property_id in DPS_PROPERTIES or enchant_type == EnchantType.PROC:
                        is_dps = True
                    
                    effects.append(EnchantEffect(
                        effect_type=enchant_type,
                        property_id=property_id,
                        value=value,
                        spell_id=spell_id,
                        scaling_type=scaling_type
                    ))
                
                if effects:  # Only store enchants with actual effects
                    enchant_data[enchant_id] = EnchantData(
                        effects=effects,
                        is_dps=is_dps
                    )
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    # Print effect type statistics
    print("\nEffect Type Statistics:")
    for effect_type, count in sorted(effect_type_counts.items()):
        try:
            effect_name = EnchantType(effect_type).name
        except ValueError:
            effect_name = "UNKNOWN"
        print(f"  {effect_name} (Type {effect_type}): {count} occurrences")
    
    print(f"\nProcessed {len(enchant_data)} enchantments")
    return enchant_data

def write_optimized_lua(output_path: Path, enchant_data: Dict[int, EnchantData]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellEnchant table for DPS calculations\n')
        f.write('--- Format: [enchantID] = { { type = "stat"|"proc"|"scaling", prop = id, value = n, spell = id, scaling = type }, ... }\n')
        f.write('HeroDBC.DBC.SpellEnchant = {\n')
        
        # Group enchants by DPS relevance for better cache locality
        dps_enchants = []
        other_enchants = []
        for enchant_id, data in enchant_data.items():
            if data.is_dps:
                dps_enchants.append(enchant_id)
            else:
                other_enchants.append(enchant_id)
        
        # Write DPS enchants first
        if dps_enchants:
            f.write('  -- DPS Enchantments\n')
            for enchant_id in sorted(dps_enchants):
                write_enchant_effects(f, enchant_id, enchant_data[enchant_id])
        
        if other_enchants:
            f.write('  -- Other Enchantments\n')
            for enchant_id in sorted(other_enchants):
                write_enchant_effects(f, enchant_id, enchant_data[enchant_id])
        
        f.write('}\n')
    
    print(f"\nWrote optimized enchantment data to {output_path}")

def write_enchant_effects(f, enchant_id: int, data: EnchantData):
    """Write enchantment effects in an optimized format."""
    f.write(f'  [{enchant_id}] = {{\n')
    for effect in sorted(data.effects, key=lambda e: e.effect_type.value):
        f.write('    {\n')
        f.write(f'      type = "{effect.effect_type.name.lower()}",\n')
        f.write(f'      prop = {effect.property_id},\n')
        f.write(f'      value = {effect.value},\n')
        if effect.spell_id > 0:
            f.write(f'      spell = {effect.spell_id},\n')
        if effect.scaling_type > 0:
            f.write(f'      scaling = {effect.scaling_type},\n')
        f.write('    },\n')
    f.write('  },\n')

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        print("Starting enchantment data processing...")
        
        # Process and write data
        enchant_data = process_enchants(generated_dir)
        write_optimized_lua(output_dir / 'SpellEnchant.lua', enchant_data)
        print('SpellEnchant data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing enchantment data: {e}')
        raise

if __name__ == '__main__':
    main()