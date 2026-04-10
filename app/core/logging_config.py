import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s:%(funcName)s:%(lineno)d | "
        "%(message)s"
    )
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        ]
    )
    
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")