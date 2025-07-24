import json
from pathlib import Path
from loguru import logger

def load_storage(storage_path):
    try:
        file = Path(storage_path)
        if file.exists():
            return json.loads(file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Could not load {storage_path}: {e}")
    return {}