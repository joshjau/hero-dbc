# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Kutikuti
Conduits Parser - Generates Conduits data from DBC files
Mapping:
SoulbindConduitRank.id_spell = SpellName.id
SoulbindConduitRank.id_parent = SoulbindConduit.id
SoulbindConduit.id_spec_set = SpecSetMember.id_parent
"""

import sys
import os
import csv
import json
from collections import OrderedDict

# Define directories
generatedDir = os.path.join('scripts', 'DBC', 'generated')
parsedDir = os.path.join('scripts', 'DBC', 'parsed')
addonEnumDir = os.path.join('HeroDBC', 'DBC')

# Change to project root directory
os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

def load_csv_data(file_name):
    """Load CSV data into dictionary with error handling"""
    try:
        with open(os.path.join(generatedDir, f'{file_name}.csv')) as csvfile:
            reader = csv.DictReader(csvfile, escapechar='\\')
            return {int(row['id']): row for row in reader}
    except Exception as e:
        print(f"Error loading {file_name}.csv: {str(e)}")
        return {}

# Load required CSV files
db = {
    'SpecSetMember': load_csv_data('SpecSetMember'),
    'SpellName': load_csv_data('SpellName')
}

def process_conduits():
    """Process conduit data from SoulbindConduitRank.csv"""
    conduits = []
    try:
        with open(os.path.join(generatedDir, 'SoulbindConduitRank.csv')) as csvfile:
            reader = csv.DictReader(csvfile, escapechar='\\')
            current_id = 0
            
            for row in sorted(reader, key=lambda d: int(d['id_parent'])):
                conduit_id = int(row['id_parent'])
                spell_id = int(row['id_spell'])
                
                if spell_id > 0 and current_id != conduit_id:
                    current_id = conduit_id
                    
                    if spell_id not in db['SpellName']:
                        continue
                        
                    conduit = {
                        'conduitId': conduit_id,
                        'conduitSpellID': spell_id,
                        'conduitName': db['SpellName'][spell_id]['name'],
                        'ranks': []  # Add rank information
                    }
                    conduits.append(conduit)
                
                # Add rank data for each conduit
                if current_id == conduit_id:
                    conduits[-1]['ranks'].append({
                        'rank': int(row['rank']),
                        'spellID': spell_id
                    })
                    
        return conduits
    except Exception as e:
        print(f"Error processing conduits: {str(e)}")
        return []

def add_spec_data(conduits):
    """Add spec data to conduits from SoulbindConduit.csv"""
    try:
        with open(os.path.join(generatedDir, 'SoulbindConduit.csv')) as csvfile:
            reader = csv.DictReader(csvfile, escapechar='\\')
            conduit_data = {int(row['id']): row for row in reader}
            
            for conduit in conduits:
                if conduit['conduitId'] in conduit_data:
                    row = conduit_data[conduit['conduitId']]
                    powerIdSpecSetMember = row['id_spec_set']
                    
                    if powerIdSpecSetMember != '0':
                        conduit['specs'] = [
                            int(entry['id_spec'])
                            for entry in db['SpecSetMember'].values()
                            if entry['id_parent'] == powerIdSpecSetMember
                        ]
                        conduit['conduitType'] = int(row['type'])
    except Exception as e:
        print(f"Error adding spec data: {str(e)}")

# Main processing
Conduits = process_conduits()
add_spec_data(Conduits)

# Output JSON
try:
    with open(os.path.join(parsedDir, 'Conduits.json'), 'w') as jsonFile:
        json.dump(Conduits, jsonFile, indent=4, sort_keys=True)
except Exception as e:
    print(f"Error writing JSON output: {str(e)}")

# Output Lua
try:
    with open(os.path.join(addonEnumDir, 'SpellConduits.lua'), 'w', encoding='utf-8') as file:
        file.write('HeroDBC.DBC.SpellConduits = {\n')
        for conduit in Conduits:
            file.write(f"  [{conduit['conduitId']}] = {conduit['conduitSpellID']},\n")
        file.write('}\n')
except Exception as e:
    print(f"Error writing Lua output: {str(e)}")
