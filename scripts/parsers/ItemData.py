# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
"""

import sys
import os
import csv
import json
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum, auto

generatedDir = os.path.join('scripts', 'DBC', 'generated')
parsedDir = os.path.join('scripts', 'DBC', 'parsed')

os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

class ItemType(Enum):
    HEAD = 1
    NECK = 2
    SHOULDERS = 3
    CHEST = 5
    WAIST = 6
    LEGS = 7
    FEET = 8
    WRISTS = 9
    HANDS = 10
    FINGER = 11
    TRINKET = 12
    WEAPON = 13
    SHIELD = 14
    RANGED = 15
    BACK = 16
    TWO_HAND_WEAPON = 17
    CHEST_ALT = 20

class ArmorType(Enum):
    PLATE = 6
    MAIL = 5
    LEATHER = 8
    CLOTH = 7

class StatType(Enum):
    AGI = 3
    STR = 4
    INT = 5
    STAM = 7
    CRIT = 32
    HASTE = 36
    VERS = 40
    MASTERY = 49
    BONUS_ARMOR = 50
    LEECH = 62
    AVOIDANCE = 63
    AGI_STR_INT = 71
    AGI_STR = 72
    AGI_INT = 73
    STR_INT = 74

@dataclass
class ItemData:
    """Store item data with type information."""
    id: int
    name: str
    ilevel: int
    type: str
    material: str
    stats: List[str]
    gems: int
    source: str

def get_item_type(inv_type: int) -> str:
    """Get item type string from inventory type ID."""
    try:
        return ItemType(inv_type).name.lower().replace('_', '')
    except ValueError:
        return ''

def get_armor_type(material: int) -> str:
    """Get armor material type string from material ID."""
    try:
        return ArmorType(material).name.lower()
    except ValueError:
        return ''

def get_stat_type(stat_type: int) -> str:
    """Get stat type string from stat type ID."""
    try:
        return StatType(stat_type).name.lower()
    except ValueError:
        return ''

def compute_gem_slots(row: Dict[str, str]) -> int:
    """Calculate number of gem slots from item data."""
    gem_count = 0
    for i in range(1, 4):
        if int(row[f'socket_color_{i}']) != 0:
            gem_count += 1
    return gem_count

def get_item_source(item_id: int, ilvl: int, encounters: Dict[int, int]) -> str:
    """Determine item source based on item level and encounter data."""
    if ilvl == 158:
        return "dungeon" if item_id in encounters else "pvp"
    elif ilvl == 200:
        return "castle_nathria" if item_id in encounters else "other"
    elif ilvl in (226, 233):
        return "sanctum_of_domination"
    return ""

def get_item_stats(row: Dict[str, str]) -> List[str]:
    """Get list of item stats from item data."""
    stats = []
    for i in range(1, 6):
        stat_type = int(row[f'stat_type_{i}'])
        stat = get_stat_type(stat_type)
        if stat:
            stats.append(stat)
    return stats

def process_item_data(encounters: Dict[int, int]) -> Dict[str, Any]:
    """Process item data from ItemSparse.csv."""
    valid_items: Dict[str, Any] = {}
    
    with open(os.path.join(generatedDir, 'ItemSparse.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            ilvl = int(row['ilevel'])
            if ilvl not in (158, 200, 226, 233):
                continue
                
            item_type = get_item_type(int(row['inv_type']))
            if not item_type:
                continue
                
            item_data = ItemData(
                id=int(row['id']),
                name=row['name'],
                ilevel=ilvl,
                type=item_type,
                material=get_armor_type(int(row['material'])),
                stats=get_item_stats(row),
                gems=compute_gem_slots(row),
                source=get_item_source(int(row['id']), ilvl, encounters)
            )
            
            # Organize items by type and material
            if item_type not in ('trinket', 'neck', 'finger', 'back'):
                if item_type not in valid_items:
                    valid_items[item_type] = {}
                if item_data.material not in valid_items[item_type]:
                    valid_items[item_type][item_data.material] = []
                valid_items[item_type][item_data.material].append(item_data.__dict__)
            else:
                if item_type not in valid_items:
                    valid_items[item_type] = []
                valid_items[item_type].append(item_data.__dict__)
    
    return valid_items

def load_encounters() -> Dict[int, int]:
    """Load encounter data from JournalEncounterItem.csv."""
    encounters = {}
    with open(os.path.join(generatedDir, 'JournalEncounterItem.csv')) as csvfile:
        reader = csv.DictReader(csvfile, escapechar='\\')
        for row in reader:
            encounters[int(row['id_item'])] = int(row['id_encounter'])
    return encounters

def write_json_output(item_data: Dict[str, Any]):
    """Write the optimized JSON output file."""
    output_path = os.path.join(parsedDir, 'ItemData.json')
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(item_data, file, indent=4)

def main():
    # Load encounter data
    encounters = load_encounters()
    
    # Process item data
    item_data = process_item_data(encounters)
    
    # Generate output
    write_json_output(item_data)

if __name__ == '__main__':
    main()
