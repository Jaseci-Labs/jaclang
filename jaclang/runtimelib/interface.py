"""Jaclang Runtimelib interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Iterable, Type, TypeVar

_ID = TypeVar("_ID")
_ANCHOR = TypeVar("_ANCHOR", bound="Anchor")
_ARCHITYPE = TypeVar("_ARCHITYPE", bound="Architype")

_BASE_ANCHOR = TypeVar("_BASE_ANCHOR", bound="Anchor")

_SERIALIZE = TypeVar("_SERIALIZE")
_DESERIALIZE = TypeVar("_DESERIALIZE")


@dataclass(eq=False, repr=False, kw_only=True)
class JID(Generic[_ID, _ANCHOR], ABC):
    """Jaclang ID Interface."""

    id: _ID
    type: Type[_ANCHOR]
    name: str

    @property
    @abstractmethod
    def anchor(self) -> _ANCHOR | None:
        """Get anchor by id and type."""

    @abstractmethod
    def __repr__(self) -> str:
        """Override string representation."""

    @abstractmethod
    def __str__(self) -> str:
        """Override string parsing."""

    @abstractmethod
    def __eq__(self, value: object) -> bool:
        """Override equal operation."""


@dataclass
class Anchor(Generic[_ID, _ARCHITYPE, _SERIALIZE], ABC):
    """Anchor Interface."""

    jid: JID[_ID, "Anchor"]
    architype: _ARCHITYPE

    @abstractmethod
    def __serialize__(self) -> _SERIALIZE:
        """Override string representation."""

    @classmethod
    @abstractmethod
    def __deserialize__(cls: Type[_DESERIALIZE], data: _SERIALIZE) -> _DESERIALIZE:
        """Override string parsing."""


@dataclass
class NodeAnchor(Anchor[_ID, "NodeArchitype", _SERIALIZE]):
    """NodeAnchor Interface."""

    edge_ids: Iterable[JID[_ID, "EdgeAnchor"]]


@dataclass
class EdgeAnchor(Anchor[_ID, "EdgeArchitype", _SERIALIZE]):
    """EdgeAnchor Interface."""

    source_id: JID[_ID, "NodeAnchor"]
    target_id: JID[_ID, "NodeAnchor"]


@dataclass
class WalkerAnchor(Anchor[_ID, "WalkerArchitype", _SERIALIZE]):
    """WalkerAnchor Interface."""


class Architype(Generic[_BASE_ANCHOR, _SERIALIZE], ABC):
    """Architype Interface."""

    __jac__: _BASE_ANCHOR

    @abstractmethod
    def __serialize__(self) -> _SERIALIZE:
        """Override string representation."""

    @classmethod
    @abstractmethod
    def __deserialize__(cls: Type[_DESERIALIZE], data: _SERIALIZE) -> _DESERIALIZE:
        """Override string parsing."""


class NodeArchitype(Architype[NodeAnchor, _SERIALIZE]):
    """NodeArchitype Interface."""


class EdgeArchitype(Architype[EdgeAnchor, _SERIALIZE]):
    """EdgeArchitype Interface."""


class WalkerArchitype(Architype[WalkerAnchor, _SERIALIZE]):
    """Walker Architype Interface."""
