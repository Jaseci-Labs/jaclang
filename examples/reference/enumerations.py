from __future__ import annotations
from enum import Enum, auto


class Color(Enum):
    Red = auto()
    Green = auto()
    Blue = auto()
    Black = auto()


print(Color.Black.value)
print(Color.Green.value)
