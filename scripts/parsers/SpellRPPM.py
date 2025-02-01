# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

Column mappings for CSV files:
SpellProcsPerMinute.csv:
    - id: Spell ID
    - ppm: Procs per minute base value

SpellProcsPerMinuteMod.csv:
    - id_parent: Parent spell ID
    - id_chr_spec: Specialization ID
    - coefficient: Modifier coefficient
    - unk_1: Modifier type (1=Haste, 2=Crit, 3=Class, 4=Spec, 5=Race, 6=Item Level, 7=Player Level, 8=Content Tuning)
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Constants for RPPM types
class ProcType(Enum):
    """Types of RPPM procs for better categorization."""
    DAMAGE = 'damage'  # Direct damage procs
    STAT = 'stat'      # Stat increase procs
    UTILITY = 'utility'  # Other effects

@dataclass
class RPPMData:
    """Store RPPM data with type information."""
    base_ppm: float
    proc_type: ProcType
    modifiers: Dict[str, float]  # Modifier type -> value

class ModifierType(Enum):
    """Types of RPPM modifiers."""
    HASTE = 1          # Affected by haste
    CRIT = 2           # Affected by crit
    CLASS = 3          # Class-specific modifier
    SPEC = 4           # Spec-specific modifier
    RACE = 5           # Race-specific modifier
    ITEM_LEVEL = 6     # Item level scaling
    PLAYER_LEVEL = 7   # Player level scaling
    CONTENT_TUNING = 8 # Content tuning modifier (e.g., raid/dungeon scaling)
    UNKNOWN = 999      # Fallback for unrecognized types

# Mapping of spec IDs to proc types
SPEC_TO_PROC_TYPE = {
    # DPS specs
    71: ProcType.DAMAGE,  # Arms
    72: ProcType.DAMAGE,  # Fury
    265: ProcType.DAMAGE, # Affliction
    266: ProcType.DAMAGE, # Demonology
    267: ProcType.DAMAGE, # Destruction
    # Tank specs
    73: ProcType.UTILITY,  # Protection
    104: ProcType.UTILITY, # Guardian
    268: ProcType.UTILITY, # Brewmaster
    # Healer specs
    105: ProcType.UTILITY, # Restoration
    256: ProcType.UTILITY, # Discipline
    257: ProcType.UTILITY, # Holy
}

def load_base_ppm(generated_dir: Path) -> Dict[int, float]:
    """Load and validate base PPM values."""
    ppm_data = {}
    with open(generated_dir / 'SpellProcsPerMinute.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        for row in reader:
            ppm_id = int(row['id'])
            ppm_value = float(row['ppm'])
            if ppm_value > 0:  # Only store meaningful PPM values
                ppm_data[ppm_id] = ppm_value
    print(f"Loaded {len(ppm_data)} base PPM values")
    return ppm_data

def determine_proc_type(spec_id: int, misc_value: int) -> ProcType:
    """Determine proc type based on spec and misc value."""
    if spec_id in SPEC_TO_PROC_TYPE:
        return SPEC_TO_PROC_TYPE[spec_id]
    
    # Use misc value to determine type if spec not found
    if misc_value in (1792, 917504, 33554432, 1879048192):  # Rating values
        return ProcType.STAT
    return ProcType.DAMAGE  # Default to damage for unknown

def process_modifiers(generated_dir: Path, base_ppm: Dict[int, float]) -> Dict[int, RPPMData]:
    """Process RPPM modifiers with improved categorization."""
    rppm_data: Dict[int, RPPMData] = {}
    modifier_type_counts: Dict[int, int] = {}  # Track frequency of modifier types
    
    with open(generated_dir / 'SpellProcsPerMinuteMod.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        # Get the actual column names from the CSV
        columns = reader.fieldnames
        print(f"Available columns in SpellProcsPerMinuteMod.csv: {', '.join(columns)}")
        
        # Find the correct misc value column name
        misc_column = None
        for possible_name in ['misc_value_1', 'misc_value', 'misc_val_1', 'misc']:
            if possible_name in columns:
                misc_column = possible_name
                break
                
        if not misc_column:
            print("Warning: Could not find misc value column in SpellProcsPerMinuteMod.csv")
            misc_column = 'misc_value_1'  # Default to avoid breaking existing logic
            
        for row in reader:
            try:
                parent_id = int(row['id_parent'])
                if parent_id not in base_ppm:
                    continue
                    
                # Initialize data if not exists
                if parent_id not in rppm_data:
                    rppm_data[parent_id] = RPPMData(
                        base_ppm=base_ppm[parent_id],
                        proc_type=determine_proc_type(
                            int(row['id_chr_spec']),
                            int(row.get(misc_column, 0))  # Use get with default 0
                        ),
                        modifiers={}
                    )
                
                # Add modifier - safely handle unknown modifier types
                mod_type_value = int(row['unk_1'])
                modifier_type_counts[mod_type_value] = modifier_type_counts.get(mod_type_value, 0) + 1
                
                try:
                    mod_type = ModifierType(mod_type_value)
                except ValueError:
                    print(f"Warning: Unknown modifier type {mod_type_value}, skipping... (Parent Spell ID: {parent_id})")
                    continue
                
                coefficient = float(row['coefficient'])
                
                if mod_type in (ModifierType.HASTE, ModifierType.CRIT):
                    rppm_data[parent_id].modifiers[mod_type.name.lower()] = True
                elif mod_type not in (ModifierType.UNKNOWN, ModifierType.ITEM_LEVEL, ModifierType.PLAYER_LEVEL, ModifierType.CONTENT_TUNING):
                    # Only process relevant modifiers for DPS calculations
                    spec_id = int(row['id_chr_spec'])
                    rppm_data[parent_id].modifiers[f"{mod_type.name.lower()}_{spec_id}"] = coefficient
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    # Print modifier type statistics
    print("\nModifier Type Statistics:")
    for mod_type_value, count in sorted(modifier_type_counts.items()):
        try:
            mod_type = ModifierType(mod_type_value).name
        except ValueError:
            mod_type = "UNKNOWN"
        print(f"  {mod_type} (Type {mod_type_value}): {count} occurrences")
    
    print(f"\nProcessed {len(rppm_data)} RPPM entries with modifiers")
    return rppm_data

def write_optimized_lua(output_path: Path, rppm_data: Dict[int, RPPMData]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized SpellRPPM table for DPS calculations\n')
        f.write('--- Format: [spellID] = { base = ppm, type = "damage"|"stat"|"utility", mods = {...} }\n')
        f.write('HeroDBC.DBC.SpellRPPM = {\n')
        
        # Group by proc type for better cache locality
        by_type: Dict[ProcType, List[int]] = {t: [] for t in ProcType}
        for spell_id, data in rppm_data.items():
            by_type[data.proc_type].append(spell_id)
        
        # Write damage procs first (most important for DPS)
        for proc_type in ProcType:
            if not by_type[proc_type]:
                continue
                
            f.write(f'  -- {proc_type.value.title()} Procs\n')
            for spell_id in sorted(by_type[proc_type]):
                data = rppm_data[spell_id]
                f.write(f'  [{spell_id}] = {{\n')
                f.write(f'    base = {data.base_ppm},\n')
                f.write(f'    type = "{data.proc_type.value}",\n')
                if data.modifiers:
                    f.write('    mods = {\n')
                    for mod_name, mod_value in sorted(data.modifiers.items()):
                        if isinstance(mod_value, bool):
                            f.write(f'      {mod_name} = true,\n')
                        else:
                            f.write(f'      {mod_name} = {mod_value},\n')
                    f.write('    },\n')
                f.write('  },\n')
        
        f.write('}\n')
    
    print(f"\nWrote optimized RPPM data to {output_path}")

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        print("Starting RPPM data processing...")
        
        # Load and process data
        base_ppm = load_base_ppm(generated_dir)
        rppm_data = process_modifiers(generated_dir, base_ppm)
        
        # Generate optimized output
        write_optimized_lua(output_dir / 'SpellRPPM.lua', rppm_data)
        print('SpellRPPM data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing RPPM data: {e}')
        raise

if __name__ == '__main__':
    main()
