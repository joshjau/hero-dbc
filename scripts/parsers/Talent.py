# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Optimized for DPS calculations and performance

Column mappings for CSV files:
Talent.csv:
    - id: Talent ID
    - id_spec: Specialization ID
    - col: Column in talent tree (0-based)
    - row: Row in talent tree (0-based)
    - id_spell_1: Primary spell ID
    - id_spell_2: Secondary spell ID (if any)
    - node_type: Type of talent node
"""

import sys
import os
import csv
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class TalentType(Enum):
    """Types of talent nodes."""
    ACTIVE = 1      # Active ability
    PASSIVE = 2     # Passive effect
    CHOICE = 3      # Choice node
    MODIFIER = 4    # Ability modifier
    OTHER = 999     # Other types

@dataclass
class TalentNode:
    """Store talent node data."""
    node_type: TalentType
    spells: List[int]  # Primary and secondary spell IDs
    col: int           # Column in talent tree
    row: int           # Row in talent tree
    is_dps: bool = False  # Whether it affects DPS

@dataclass
class SpecTalents:
    """Store specialization talent data."""
    talents: Dict[int, TalentNode]  # Talent ID -> Node data
    is_dps_spec: bool = False       # Whether this is a DPS spec

# DPS specializations
DPS_SPECS = {
    71,   # Arms Warrior
    72,   # Fury Warrior
    265,  # Affliction Warlock
    266,  # Demonology Warlock
    267,  # Destruction Warlock
    # Add other DPS specs here
}

def process_talents(generated_dir: Path) -> Dict[int, Dict[int, TalentNode]]:
    """Process talent data with improved categorization."""
    talent_data: Dict[int, Dict[int, TalentNode]] = {}  # Spec ID -> {Talent ID -> Node}
    node_type_counts: Dict[int, int] = {}  # Track frequency of node types
    
    with open(generated_dir / 'Talent.csv') as f:
        reader = csv.DictReader(f, escapechar='\\')
        print(f"Available columns in Talent.csv: {', '.join(reader.fieldnames)}")
        
        for row in reader:
            try:
                talent_id = int(row['id'])
                spec_id = int(row['id_spec'])
                
                # Initialize spec data if needed
                if spec_id not in talent_data:
                    talent_data[spec_id] = {}
                
                # Get spell IDs
                spells = []
                for i in range(1, 3):  # Check both spell slots
                    spell_id = int(row.get(f'id_spell_{i}', 0))
                    if spell_id > 0:
                        spells.append(spell_id)
                
                # Skip empty talents
                if not spells:
                    continue
                
                node_type_value = int(row.get('node_type', 0))
                node_type_counts[node_type_value] = node_type_counts.get(node_type_value, 0) + 1
                
                try:
                    node_type = TalentType(node_type_value)
                except ValueError:
                    print(f"Warning: Unknown node type {node_type_value} for talent {talent_id}")
                    node_type = TalentType.OTHER
                
                # Create talent node
                talent_data[spec_id][talent_id] = TalentNode(
                    node_type=node_type,
                    spells=spells,
                    col=int(row['col']),
                    row=int(row['row']),
                    is_dps=(spec_id in DPS_SPECS)
                )
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Error processing row: {e}")
                continue
    
    # Print node type statistics
    print("\nNode Type Statistics:")
    for node_type_value, count in sorted(node_type_counts.items()):
        try:
            node_name = TalentType(node_type_value).name
        except ValueError:
            node_name = "UNKNOWN"
        print(f"  {node_name} (Type {node_type_value}): {count} occurrences")
    
    print(f"\nProcessed talents for {len(talent_data)} specializations")
    return talent_data

def write_optimized_lua(output_path: Path, talent_data: Dict[int, Dict[int, TalentNode]]):
    """Write optimized Lua output for faster runtime access."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('--- ============================ HEADER ============================\n')
        f.write('--- Optimized Talent table for DPS calculations\n')
        f.write('--- Format: [specID] = { [talentID] = { type = "active"|"passive"|etc, spells = {id1, id2}, col = n, row = n } }\n')
        f.write('HeroDBC.DBC.Talent = {\n')
        
        # Write DPS specs first for better cache locality
        dps_specs = []
        other_specs = []
        for spec_id in talent_data.keys():
            if spec_id in DPS_SPECS:
                dps_specs.append(spec_id)
            else:
                other_specs.append(spec_id)
        
        # Write DPS specs first
        if dps_specs:
            f.write('  -- DPS Specializations\n')
            for spec_id in sorted(dps_specs):
                write_spec_talents(f, spec_id, talent_data[spec_id])
        
        if other_specs:
            f.write('  -- Other Specializations\n')
            for spec_id in sorted(other_specs):
                write_spec_talents(f, spec_id, talent_data[spec_id])
        
        f.write('}\n')
    
    print(f"\nWrote optimized talent data to {output_path}")

def write_spec_talents(f, spec_id: int, talents: Dict[int, TalentNode]):
    """Write specialization talents in an optimized format."""
    f.write(f'  [{spec_id}] = {{\n')
    for talent_id, node in sorted(talents.items(), key=lambda x: (x[1].row, x[1].col)):
        f.write(f'    [{talent_id}] = {{\n')
        f.write(f'      type = "{node.node_type.name.lower()}",\n')
        f.write('      spells = {')
        f.write(', '.join(str(spell_id) for spell_id in node.spells))
        f.write('},\n')
        f.write(f'      col = {node.col},\n')
        f.write(f'      row = {node.row},\n')
        f.write('    },\n')
    f.write('  },\n')

def main():
    """Main execution function."""
    # Setup paths
    root_dir = Path(__file__).parent.parent.parent
    generated_dir = root_dir / 'scripts' / 'DBC' / 'generated'
    output_dir = root_dir / 'HeroDBC' / 'DBC'
    
    try:
        print("Starting talent data processing...")
        
        # Process and write data
        talent_data = process_talents(generated_dir)
        write_optimized_lua(output_dir / 'Talent.lua', talent_data)
        print('Talent data optimized successfully.')
        
    except Exception as e:
        print(f'Error processing talent data: {e}')
        raise

if __name__ == '__main__':
    main()
