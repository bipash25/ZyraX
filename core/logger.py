"""
Structured logging system for ZyraX bot
Provides console and file logging with colors and formatting
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': Colors.GRAY,
        'INFO': Colors.BLUE,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA + Colors.BOLD
    }
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, Colors.RESET)
        record.levelname = f"{level_color}{record.levelname:8s}{Colors.RESET}"
        
        # Add color to logger name
        record.name = f"{Colors.CYAN}{record.name}{Colors.RESET}"
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(
        fmt=f"{Colors.GRAY}%(asctime)s{Colors.RESET} | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Log initialization message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at {level} level")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)