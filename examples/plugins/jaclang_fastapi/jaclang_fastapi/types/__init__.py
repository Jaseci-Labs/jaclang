"""JacLang FastAPI Types."""

from dataclasses import field
from typing import List, Optional

from fastapi import UploadFile as File

OptFile = Optional[File]
Files = List[File]
OptFiles = Optional[Files]


class Defaults:
    """Field Default Handler."""

    NONE = field(default=None)
    LIST = field(default_factory=list)
    DICT = field(default_factory=dict)
    SET = field(default_factory=set)
    BYTES = field(default_factory=bytes)
    STR = field(default_factory=str)


__all__ = ["File", "Files", "OptFile", "OptFiles", "Defaults"]
