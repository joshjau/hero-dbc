# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

Column mappings for CSV files:
ItemEffect.csv:
    - id_parent: Parent item ID
    - id_spell: Spell ID
    - trigger_type: How the spell is triggered (0=use, 1=equip, 2=proc)
    - charges: Number of charges (-1 for infinite)
    - cooldown_category: Cooldown category ID
    - cooldown_category_duration: Category cooldown in milliseconds
    - cooldown_duration: Individual cooldown in milliseconds
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class TriggerType(Enum):
    """Types of item spell triggers."""
    USE = 0      # On-use effects
    EQUIP = 1    # Passive equip effects
    PROC = 2     # Proc effects
    OTHER = 999  # Other trigger types

@dataclass
class ItemSpellData:
    """Store item spell data with type information."""
    spell_id: int
    trigger_type: TriggerType
    charges: int = -1  # -1 for infinite
    cooldown: int = 0  # In milliseconds
    shared_cd: int = 0  # Category cooldown in milliseconds
    cd_category: int = 0  # Cooldown category ID

def process_item_spells(generated_dir: Path) -> Dict[int, List[ItemSpellData]]:
    """Process item spell data with improved categorization."""
    item_data: Dict[int, List[ItemSpellData]] = {}
    trigger_type_counts: Dict[int, int] = {}  # Track frequency of trigger types
    
    with open(generated_dir / 'ItemEffect.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        print(f"Available columns in ItemEffect.csv: {', '.join(reader.fieldnames)}")
        
        for row in reader:
            try:
                item_id = int(row['id_parent'])
                spell_id = int(row['id_spell'])
                
                # Skip invalid entries
                if spell_id == 0:
                    continue
                
                trigger_value = int(row['trigger_type'])
                trigger_type_counts[trigger_value] = trigger_type_counts.get(trigger_value, 0) + 1
                
                try:
                    trigger_type = TriggerType(trigger_value)
                except ValueError:
                    print(f"Warning: Unknown trigger type {trigger_value} for item {item_id}")
                    trigger_type = TriggerType.OTHER
                
                # Initialize list if needed
                if item_id not in item_data:
                    item_data[item_id] = []
                
                # Get cooldown information
                cd_category = int(row.get('cooldown_category', 0))
                shared_cd = int(row.get('cooldown_category_duration', 0))
                cooldown = int(row.get('cooldown_duration', 0))
                charges = int(row.get('charges', -1))
                
                item_data[item_id].append(ItemSpellData(
                    spell_id=spell_id,
                    trigger_type=trigger_type,
                    charges=charges,
                    cooldown=cooldown,
                    shared_cd=shared_cd,
                    cd_category=cd_category
                ))
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    # Print trigger type statistics
    print("\nTrigger Type Statistics:")
    for trigger_value, count in sorted(trigger_type_counts.items()):
        try:
            trigger_name = TriggerType(trigger_value).name
        except ValueError:
            trigger_name = "UNKNOWN"
        print(f"  {trigger_name} (Type {trigger_value}): {count} occurrences")
    
    print(f"\nProcessed {len(item_data)} items with spell effects")
    return item_data

def write_optimized_lua(output_path: Path, item_data: Dict[int, List[ItemSpellData]]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized ItemSpell table for DPS calculations\n')
        f.write('--- Format: [itemID] = { { spell = id, trigger = "use"|"equip"|"proc", cd = ms, shared_cd = ms, cd_cat = id, charges = n }, ... }\n')
        f.write('HeroDBC.DBC.ItemSpell = {\n')
        
        # Group items by trigger type for better cache locality
        by_type: Dict[TriggerType, List[int]] = {t: [] for t in TriggerType}
        for item_id, spells in item_data.items():
            # Use most important trigger type for categorization
            main_type = min(spell.trigger_type for spell in spells)
            by_type[main_type].append(item_id)
        
        # Write procs first (most important for DPS)
        for trigger_type in sorted(TriggerType, key=lambda t: t.value):
            if not by_type[trigger_type]:
                continue
                
            f.write(f'  -- {trigger_type.name.title()} Effects\n')
            for item_id in sorted(by_type[trigger_type]):
                write_item_spells(f, item_id, item_data[item_id])
        
        f.write('}\n')
    
    print(f"\nWrote optimized item spell data to {output_path}")

def write_item_spells(f, item_id: int, spells: List[ItemSpellData]):
    """Write item spells in an optimized format."""
    f.write(f'  [{item_id}] = {{\n')
    for spell in sorted(spells, key=lambda s: (s.trigger_type.value, s.spell_id)):
        f.write('    {\n')
        f.write(f'      spell = {spell.spell_id},\n')
        f.write(f'      trigger = "{spell.trigger_type.name.lower()}",\n')
        if spell.cooldown > 0:
            f.write(f'      cd = {spell.cooldown},\n')
        if spell.shared_cd > 0:
            f.write(f'      shared_cd = {spell.shared_cd},\n')
        if spell.cd_category > 0:
            f.write(f'      cd_cat = {spell.cd_category},\n')
        if spell.charges != -1:
            f.write(f'      charges = {spell.charges},\n')
        f.write('    },\n')
    f.write('  },\n')

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        print("Starting item spell data processing...")
        
        # Process and write data
        item_data = process_item_spells(generated_dir)
        write_optimized_lua(output_dir / 'ItemSpell.lua', item_data)
        print('ItemSpell data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing item spell data: {e}')
        raise

if __name__ == '__main__':
    main()
