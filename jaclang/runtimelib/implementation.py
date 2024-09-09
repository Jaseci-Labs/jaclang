"""Jaclang Runtimelib Implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Type

from .interface import (
    JID as _JID,
    Anchor as _Anchor,
    _ANCHOR,
    NodeAnchor as _NodeAnchor,
    EdgeAnchor as _EdgeAnchor,
    WalkerAnchor as _WalkerAnchor,
    Architype as _Architype,
    NodeArchitype as _NodeArchitype,
    EdgeArchitype as _EdgeArchitype,
    WalkerArchitype as _WalkerArchitype,
)


@dataclass
class JID(_JID[UUID, _ANCHOR]):
    """Jaclang Default JID."""

    id: UUID
    type: Type[_ANCHOR]

    @property
    def anchor(self) -> _ANCHOR | None:
        """Get anchor by id and type."""
        return None

    def __repr__(self) -> str:
        """Override string representation."""
        return f"{self.type.__class__.__name__[:1].lower()}:{self.name}:{self.id}"

    def __str__(self) -> str:
        """Override string parsing."""
        return f"{self.type.__class__.__name__[:1].lower()}:{self.name}:{self.id}"


@dataclass
class NodeAnchor(_NodeAnchor[JID]):
    """NodeAnchor Interface."""

    edge_ids: list[JID["EdgeAnchor"]]


@dataclass
class EdgeAnchor(_EdgeAnchor[JID]):
    """NodeAnchor Interface."""

    source_id: JID["NodeAnchor"]
    target_id: JID["NodeAnchor"]
