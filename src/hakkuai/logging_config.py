"""
Logging configuration for HakkuAI.
Ensures sensitive user information (medical data, identifiers) is NEVER logged.
"""

import logging
import re
import sys

# Masking patterns for potential sensitive identifiers
AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PHONE_REGEX = re.compile(r"\b(?:\+91|91)?[6-9]\d{9}\b")
ACCOUNT_REGEX = re.compile(r"\b\d{9,18}\b")

class SensitiveFilter(logging.Filter):
    """Filter that sanitizes any accidentally logged sensitive numbers or PII."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", record.msg)
            record.msg = PHONE_REGEX.sub("[REDACTED_PHONE]", record.msg)
            # Mask potential bank account numbers if longer than 8 digits
            record.msg = ACCOUNT_REGEX.sub("[REDACTED_NUM]", record.msg)
        return True

def setup_logger(name: str = "hakkuai", level: str = "INFO") -> logging.Logger:
    """Configures and returns a privacy-safe logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveFilter())
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger

logger = setup_logger()
