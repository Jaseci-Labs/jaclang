"""Memory abstraction for jaseci plugin."""

from uuid import UUID

from .memory import Memory


class JacMemory(Memory[UUID]):
    """Generic Memory Handler."""

    pass
