"""
logger.py
Centralised logging configuration.

- Console handler  : INFO and above, colourised format
- File handler     : DEBUG and above, rotating daily, kept for 30 days
- Log directory    : logs/   (created automatically)
- Log filename     : logs/server_YYYY-MM-DD.log
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"

# Log format used by both handlers
_FMT     = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    console_level: int = logging.INFO,
    file_level: int    = logging.DEBUG,
    backup_count: int  = 30,
) -> None:
    """
    Call once at startup (main.py) to configure the root logger.

    Parameters
    ----------
    console_level : logging level for stdout
    file_level    : logging level written to the rotating log file
    backup_count  : number of daily log files to retain
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)   # capture everything; handlers filter

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # ── Rotating daily file handler ───────────────────────────────────────────
    log_file = LOG_DIR / f"server_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",          # rotate at midnight
        interval=1,               # every 1 day
        backupCount=backup_count,
        encoding="utf-8",
        utc=True,
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    # Suffix applied to rotated files: server_YYYY-MM-DD.log.2024-05-01
    file_handler.suffix = "%Y-%m-%d"

    # ── Attach handlers (idempotent) ──────────────────────────────────────────
    if not root.handlers:
        root.addHandler(console_handler)
        root.addHandler(file_handler)
    else:
        # Avoid duplicate handlers on re-import / hot reload
        handler_types = {type(h) for h in root.handlers}
        if logging.StreamHandler not in handler_types:
            root.addHandler(console_handler)
        if logging.handlers.TimedRotatingFileHandler not in handler_types:
            root.addHandler(file_handler)

    logging.getLogger(__name__).info(
        f"Logging initialised — console={logging.getLevelName(console_level)}, "
        f"file={logging.getLevelName(file_level)}, log_dir={LOG_DIR}"
    )
