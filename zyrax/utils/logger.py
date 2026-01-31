import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger("ZyraX")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # File handler (rotates at 10MB)
    file_handler = RotatingFileHandler(
        'logs/zyrax.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    ))
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

logging.basicConfig(level=logging.ERROR) # Mute other loggers
logger = setup_logger()
