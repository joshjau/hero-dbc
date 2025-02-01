import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dbc_parser.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def validate_csv_columns(reader, required_columns):
    """Validate that required columns exist in CSV."""
    missing = [col for col in required_columns if col not in reader.fieldnames]
    if missing:
        logger.warning(f"Missing columns in CSV: {', '.join(missing)}")
        # Try to find alternative column names
        alternatives = {}
        for col in missing:
            for possible in [col, f"{col}_1", f"{col}_2", f"misc_{col}"]:
                if possible in reader.fieldnames:
                    alternatives[col] = possible
                    break
        if alternatives:
            logger.info(f"Found alternative columns: {alternatives}")
        return False
    return True