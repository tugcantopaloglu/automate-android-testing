import logging
import sys

def setup_logger():
    """Sets up the root logger to output to console and a file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("automation.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
