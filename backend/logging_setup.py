import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

_configured = False


def setup_logging():
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handlers = [logging.FileHandler(LOG_DIR / "dashboard.log", encoding="utf-8")]
    # sys.stdout/stderr are None when launched headless via pythonw.exe (e.g. Task
    # Scheduler) — a StreamHandler would crash on the first log call in that case.
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )
    _configured = True
