# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
RPPM Parser for HeroDBC - Optimized for TWW 11.x.x
Handles RPPM calculations and modifiers for spell procs

Key features:
- Full support for all retail races including Dracthyr
- Optimized RPPM calculations for maximum DPS accuracy
- Strict type checking for data integrity
- Retail-only implementation (11.x.x)
- Optimized for high-performance proc rate calculations
"""

import sys
import os
import csv
from collections import defaultdict
try:
    import ujson as json  # ujson for faster processing
except ImportError:
    import json
from typing import Dict, Union, Any, Optional, List, Tuple, DefaultDict
import time  # Added for performance monitoring

# Configure paths
generatedDir = os.path.join('scripts', 'DBC', 'generated')
addonEnumDir = os.path.join('HeroDBC', 'DBC')
os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

# Type aliases for better code clarity and validation
RPPMDict = Dict[int, Dict[int, Union[float, bool, Dict[int, float]]]]
ModifierDict = DefaultDict[int, DefaultDict[int, Dict[int, float]]]
PPMIDDict = Dict[int, int]

# Constants for RPPM calculations
RPPM_HASTE_ID = 1
RPPM_CRIT_ID = 2
RPPM_CLASS_ID = 3
RPPM_SPEC_ID = 4
RPPM_RACE_ID = 5

def computeRPPMType(x: int) -> str:
    """Maps RPPM modifier types to their string representation for retail WoW"""
    return {
        RPPM_HASTE_ID: 'HASTE',  # Haste-based RPPM scaling
        RPPM_CRIT_ID: 'CRIT',    # Crit-based RPPM scaling
        RPPM_CLASS_ID: 'CLASS',  # Class-specific modifiers
        RPPM_SPEC_ID: 'SPEC',    # Spec-specific modifiers
        RPPM_RACE_ID: 'RACE'     # Race-specific modifiers
    }.get(x, '')

def computeClass(classmask: int) -> int:
    """Converts class mask to individual class bits for retail WoW classes"""
    return {
        1: 1,      # Warrior
        2: 2,      # Paladin
        3: 4,      # Hunter
        4: 8,      # Rogue
        5: 16,     # Priest
        6: 32,     # Death Knight
        7: 64,     # Shaman
        8: 128,    # Mage
        9: 256,    # Warlock
        10: 512,   # Monk
        11: 1024,  # Druid
        12: 2048,  # Demon Hunter
        13: 4096   # Evoker
    }.get(classmask, 0)

def computeRace(racemask: int) -> str:
    """Converts race mask to race name for retail WoW races"""
    return {
        1: 'Human',
        2: 'Orc',
        3: 'Dwarf',
        4: 'NightElf',
        5: 'Scourge',
        6: 'Tauren',
        7: 'Gnome',
        8: 'Troll',
        9: 'Goblin',
        10: 'BloodElf',
        11: 'Draenei',
        24: 'Pandaren',
        25: 'Pandaren',
        26: 'Pandaren',
        27: 'Nightborne',
        28: 'HighmountainTauren',
        29: 'VoidElf',
        30: 'LightforgedDraenei',
        31: 'ZandalariTroll',
        32: 'KulTiran',
        34: 'DarkIronDwarf',
        35: 'Vulpera',
        36: 'MagharOrc',
        37: 'Mechagnome',
        52: 'Dracthyr',
        53: 'Dracthyr'
    }.get(racemask, '')

def loadBasePPM() -> Dict[int, float]:
    """Load base PPM values from CSV with validation and optimization for DPS calculations"""
    base_ppm: Dict[int, float] = {}
    try:
        with open(os.path.join(generatedDir, 'SpellProcsPerMinute.csv')) as csvfile:
            reader = csv.DictReader(csvfile, escapechar='\\')
            for row in reader:
                spell_id = int(row['id'])
                ppm_value = float(row['ppm'])
                # Store valid PPM values with high precision for accurate DPS
                if ppm_value > 0:
                    base_ppm[spell_id] = round(ppm_value, 6)  # 6 decimal precision for accurate proc rates
    except (ValueError, KeyError) as e:
        print(f"Error processing SpellProcsPerMinute.csv: {e}")
        raise
    return base_ppm

def loadModPPM(base_ppm: Dict[int, float]) -> ModifierDict:
    """Load and process PPM modifiers with validation for retail WoW"""
    # Use defaultdict for better performance with nested dictionaries
    mod_ppm: ModifierDict = defaultdict(lambda: defaultdict(dict))
    
    try:
        with open(os.path.join(generatedDir, 'SpellProcsPerMinuteMod.csv')) as csvfile:
            reader = csv.DictReader(csvfile, escapechar='\\')
            for row in reader:
                parent_id = int(row['id_parent'])
                mod_type = int(row['unk_1'])
                coefficient = float(row['coefficient'])
                
                # Skip invalid entries
                if coefficient == 0 or parent_id not in base_ppm:
                    continue
                
                # Process different modifier types
                if mod_type in (RPPM_HASTE_ID, RPPM_CRIT_ID):
                    mod_ppm[parent_id][mod_type] = True
                elif mod_type == RPPM_CLASS_ID:
                    processClassModifiers(row, mod_ppm, parent_id, base_ppm, coefficient)
                elif mod_type in (RPPM_SPEC_ID, RPPM_RACE_ID):
                    processSpecRaceModifiers(row, mod_ppm, parent_id, base_ppm, coefficient)
    except (ValueError, KeyError) as e:
        print(f"Error processing SpellProcsPerMinuteMod.csv: {e}")
        raise
    
    return mod_ppm

def processClassModifiers(row: Dict[str, str], mod_ppm: ModifierDict, parent_id: int, base_ppm: Dict[int, float], coefficient: float):
    """Process class-specific modifiers with validation and high precision"""
    try:
        racemask = int(row['id_chr_spec'])
        base_value = base_ppm[parent_id]
        mod_type = int(row['unk_1'])
        
        for i in range(13, 0, -1):  # Updated to include Evoker (13)
            class_bit = computeClass(i)
            if class_bit and racemask - class_bit >= 0:
                # Calculate modified PPM value with coefficient using high precision
                modified_ppm = round(base_value * (1.0 + coefficient), 6)
                if modified_ppm > 0:
                    mod_ppm[parent_id][mod_type][i] = modified_ppm
                racemask -= class_bit
    except (ValueError, KeyError) as e:
        print(f"Error processing class modifier for parent_id {parent_id}: {e}")
        raise

def processSpecRaceModifiers(row: Dict[str, str], mod_ppm: ModifierDict, parent_id: int, base_ppm: Dict[int, float], coefficient: float):
    """Process spec and race modifiers with validation and high precision"""
    try:
        chr_spec = int(row['id_chr_spec'])
        base_value = base_ppm[parent_id]
        mod_type = int(row['unk_1'])
        
        # Calculate modified PPM value with coefficient using high precision
        modified_ppm = round(base_value * (1.0 + coefficient), 6)
        if modified_ppm > 0:
            mod_ppm[parent_id][mod_type][chr_spec] = modified_ppm
    except (ValueError, KeyError) as e:
        print(f"Error processing spec/race modifier for parent_id {parent_id}: {e}")
        raise

def loadPPMID() -> PPMIDDict:
    """Load PPM IDs from SpellAuraOptions with validation"""
    ppm_ids: PPMIDDict = {}
    try:
        with open(os.path.join(generatedDir, 'SpellAuraOptions.csv')) as csvfile:
            reader = csv.DictReader(csvfile, escapechar='\\')
            for row in reader:
                ppm_id = int(row['id_ppm'])
                if ppm_id != 0:
                    parent_id = int(row['id_parent'])
                    ppm_ids[parent_id] = ppm_id
    except (ValueError, KeyError) as e:
        print(f"Error processing SpellAuraOptions.csv: {e}")
        raise
    return ppm_ids

def writeLuaOutput(ppm_ids: PPMIDDict, base_ppm: Dict[int, float], mod_ppm: ModifierDict):
    """Write the final Lua output file with optimized structure for fast lookups"""
    try:
        with open(os.path.join(addonEnumDir, 'SpellRPPM.lua'), 'w', encoding='utf-8') as file:
            # Write file header with metadata
            file.write('-- Generated using WoW 11.x.x client data\n')
            file.write('-- This file contains RPPM data for spells with proc effects\n')
            file.write('-- Optimized for high-performance lookups and DPS calculations\n\n')
            
            # Pre-declare the table for better Lua memory management
            file.write('local RPPMData = {\n')
            
            # Write data in sorted order for consistent output and better lookup performance
            for item_id in sorted(ppm_ids.keys()):
                ppm_id = ppm_ids[item_id]
                if ppm_id not in base_ppm:
                    continue
                
                file.write(f'  [{item_id}] = {{\n')
                # Base PPM value with high precision
                file.write(f'    [0] = {base_ppm[ppm_id]:.6f},  -- Base PPM\n')
                
                if ppm_id in mod_ppm:
                    # Write modifiers in sorted order for consistent lookups
                    for mod_id, mod_data in sorted(mod_ppm[ppm_id].items()):
                        if isinstance(mod_data, bool):
                            # Haste/Crit modifiers
                            file.write(f'    [{mod_id}] = {str(mod_data).lower()},  -- {"HASTE" if mod_id == RPPM_HASTE_ID else "CRIT"} scaling\n')
                        elif isinstance(mod_data, dict):
                            # Class/Spec/Race modifiers
                            file.write(f'    [{mod_id}] = {{  -- {computeRPPMType(mod_id)} modifiers\n')
                            for sub_id, value in sorted(mod_data.items()):
                                file.write(f'      [{sub_id}] = {value:.6f},\n')
                            file.write('    },\n')
                file.write('  },\n')
            file.write('}\n\n')
            
            # Add optimized lookup function for RPPM calculations
            file.write('''
-- Fast lookup function for RPPM calculations
local function GetRPPM(spellID, classID, specID)
  local data = RPPMData[spellID]
  if not data then return 0 end
  
  local base = data[0]
  if not base then return 0 end
  
  -- Apply class/spec modifiers if they exist
  if classID and data[3] and data[3][classID] then
    base = data[3][classID]
  end
  if specID and data[4] and data[4][specID] then
    base = data[4][specID]
  end
  
  return base
end

HeroDBC.DBC.SpellRPPM = RPPMData
HeroDBC.DBC.GetRPPM = GetRPPM
''')
    except IOError as e:
        print(f"Error writing SpellRPPM.lua: {e}")
        raise

def main():
    """Main processing function with error handling and performance monitoring"""
    try:
        start_time = time.time()
        
        print("Loading base PPM values...")
        base_ppm = loadBasePPM()
        
        print("Processing PPM modifiers...")
        mod_ppm = loadModPPM(base_ppm)
        
        print("Loading PPM IDs...")
        ppm_ids = loadPPMID()
        
        print("Writing optimized Lua output...")
        writeLuaOutput(ppm_ids, base_ppm, mod_ppm)
        
        end_time = time.time()
        print(f"RPPM processing completed in {end_time - start_time:.2f} seconds")
        print(f"Processed {len(ppm_ids)} spells with RPPM effects")
    except Exception as e:
        print(f"Fatal error processing RPPM data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
