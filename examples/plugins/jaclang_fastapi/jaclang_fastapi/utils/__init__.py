"""Common Utilities."""

import logging
import sys
from datetime import datetime, timedelta, timezone


def utc_now(**addons: dict[str, int]) -> int:
    """Get current timestamp with option to add additional timedelta."""
    return int((datetime.now(tz=timezone.utc) + timedelta(**addons)).timestamp())


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
# logging.getLogger('passlib').setLevel(logging.ERROR)

__all__ = [
    "utc_now",
    "logger",
]
