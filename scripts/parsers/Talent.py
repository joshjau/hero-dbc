# -*- coding: utf-8 -*-
# pylint: disable=C0103
# pylint: disable=C0301

"""
@author: Quentin Giraud <dev@aethys.io>
"""

import sys
import os
import csv
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths relative to hero-dbc root
generatedDir = os.path.join('scripts', 'DBC', 'generated')
parsedDir = os.path.join('scripts', 'DBC', 'parsed')

# Change to hero-dbc root directory
os.chdir(os.path.join(os.path.dirname(sys.path[0]), '..', '..', 'hero-dbc'))

def load_db_files(db_files: list) -> Dict[str, Dict[str, Any]]:
    """Load and parse CSV files into dictionaries"""
    db = {}
    for db_file in db_files:
        file_path = os.path.join(generatedDir, f'{db_file}.csv')
        try:
            with open(file_path) as csvfile:
                reader = csv.DictReader(csvfile, escapechar='\\')
                db[db_file] = {row['id']: row for row in reader}
                logger.info(f"Successfully loaded {len(db[db_file])} entries from {db_file}.csv")
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            raise
    return db

def parse_talents(db: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Parse talent data into hierarchical structure"""
    if 'Talent' not in db or 'SpellName' not in db:
        raise ValueError("Required database files not loaded")
    
    talents = {}
    for entry_id, entry in db['Talent'].items():
        try:
            class_id = entry['class_id']
            spec_id = entry['spec_id']
            row = entry['row']
            spell_id = entry['id_spell']

            # Initialize nested dictionaries
            talents.setdefault(class_id, {}).setdefault(spec_id, {}).setdefault(row, {})

            # Build talent entry
            talents[class_id][spec_id][row][entry['col']] = {
                'talentId': int(entry['id']),
                'spellId': int(spell_id),
                'spellName': db['SpellName'][spell_id]['name'] if spell_id in db['SpellName'] else 'Unknown'
            }
        except KeyError as e:
            logger.warning(f"Missing key in talent entry {entry_id}: {str(e)}")
            continue
    
    return talents

def main():
    """Main execution function"""
    # Load database files
    db_files = ['Talent', 'SpellName']
    db = load_db_files(db_files)

    # Parse talents
    talents = parse_talents(db)

    # Write output
    output_path = os.path.join(parsedDir, 'Talent.json')
    with open(output_path, 'w') as json_file:
        json.dump(talents, json_file, indent=4, sort_keys=True)

if __name__ == '__main__':
    main()
