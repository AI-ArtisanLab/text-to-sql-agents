"""
Logging Configuration
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

import logging, os
from datetime import datetime

def get_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("text2sql")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(fh)
    return logger
