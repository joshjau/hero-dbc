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
    250: ProcType.DAMAGE, # Blood (DK)
    251: ProcType.DAMAGE, # Frost (DK)
    252: ProcType.DAMAGE, # Unholy (DK)
    259: ProcType.DAMAGE, # Assassination
    260: ProcType.DAMAGE, # Outlaw
    261: ProcType.DAMAGE, # Subtlety
    262: ProcType.DAMAGE, # Elemental
    263: ProcType.DAMAGE, # Enhancement
    264: ProcType.DAMAGE, # Restoration (for DPS procs)
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
    """Enhanced proc type determination with better DPS focus."""
    # Check if it's a known DPS spec
    if spec_id in SPEC_TO_PROC_TYPE:
        return SPEC_TO_PROC_TYPE[spec_id]
    
    # Additional checks for DPS-related misc values
    if misc_value in (
        1792,       # Attack Power
        917504,     # Spell Power
        33554432,   # Mastery
        1879048192  # Versatility
    ):
        return ProcType.DAMAGE
        
    # Default to damage for unknown procs in DPS specs
    if spec_id in range(250, 268):  # DPS spec range
        return ProcType.DAMAGE
        
    return ProcType.UTILITY

def process_modifiers(generated_dir: Path, base_ppm: Dict[int, float]) -> Dict[int, RPPMData]:
    """Process RPPM modifiers with DPS optimization focus."""
    rppm_data: Dict[int, RPPMData] = {}
    
    with open(generated_dir / 'SpellProcsPerMinuteMod.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        
        for row in reader:
            try:
                parent_id = int(row['id_parent'])
                if parent_id not in base_ppm:
                    continue
                    
                # Initialize data if not exists
                if parent_id not in rppm_data:
                    spec_id = int(row['id_chr_spec'])
                    proc_type = determine_proc_type(spec_id, int(row.get('misc_value_1', 0)))
                    
                    # Skip non-damage procs for DPS optimization
                    if proc_type != ProcType.DAMAGE:
                        continue
                        
                    rppm_data[parent_id] = RPPMData(
                        base_ppm=base_ppm[parent_id],
                        proc_type=proc_type,
                        modifiers={}
                    )
                
                # Process modifiers that affect DPS
                mod_type_value = int(row['unk_1'])
                try:
                    mod_type = ModifierType(mod_type_value)
                except ValueError:
                    continue
                
                coefficient = float(row['coefficient'])
                
                # Handle different modifier types with numeric values
                if mod_type == ModifierType.HASTE:
                    rppm_data[parent_id].modifiers['haste'] = coefficient
                elif mod_type == ModifierType.CRIT:
                    rppm_data[parent_id].modifiers['crit'] = coefficient
                elif mod_type == ModifierType.SPEC:
                    spec_id = int(row['id_chr_spec'])
                    rppm_data[parent_id].modifiers[f"spec_{spec_id}"] = coefficient
                elif mod_type == ModifierType.CLASS:
                    rppm_data[parent_id].modifiers['class'] = coefficient
                
            except (ValueError, KeyError):
                continue
    
    return rppm_data

def write_optimized_lua(output_path: Path, rppm_data: Dict[int, RPPMData]):
    """Write Lua output optimized for DPS calculations."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('HeroDBC.DBC.SpellRPPM = {\n')
        
        # Sort by spell ID for consistent access
        for spell_id in sorted(rppm_data.keys()):
            data = rppm_data[spell_id]
            
            # Only write damage procs
            if data.proc_type != ProcType.DAMAGE:
                continue
                
            f.write(f'  [{spell_id}] = {{\n')
            f.write(f'    base = {data.base_ppm},\n')
            f.write(f'    type = "{data.proc_type.value}",\n')
            
            if data.modifiers:
                f.write('    mods = {\n')
                # Sort modifiers for consistent access
                for mod_name, mod_value in sorted(data.modifiers.items()):
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
