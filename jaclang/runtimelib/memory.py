"""Core constructs for Jac Language."""

from __future__ import annotations

from dataclasses import dataclass, field
from pickle import dumps
from shelve import Shelf, open
from typing import Callable, Generator, Generic, Iterable, TypeVar
from uuid import UUID

from .architype import Anchor, NodeAnchor, Root, TANCH

ID = TypeVar("ID")


@dataclass
class Memory(Generic[ID, TANCH]):
    """Generic Memory Handler."""

    __mem__: dict[ID, TANCH] = field(default_factory=dict)
    __gc__: set[ID] = field(default_factory=set)

    def close(self) -> None:
        """Close memory handler."""
        self.__mem__.clear()
        self.__gc__.clear()

    def find(
        self,
        ids: ID | Iterable[ID],
        filter: Callable[[TANCH], TANCH] | None = None,
    ) -> Generator[TANCH, None, None]:
        """Find anchors from memory by ids with filter."""
        if not isinstance(ids, Iterable):
            ids = [ids]

        return (
            anchor
            for id in ids
            if (anchor := self.__mem__.get(id)) and (not filter or filter(anchor))
        )

    def find_one(
        self,
        ids: ID | Iterable[ID],
        filter: Callable[[TANCH], TANCH] | None = None,
    ) -> TANCH | None:
        """Find one anchor from memory by ids with filter."""
        return next(self.find(ids, filter), None)

    def set(self, id: ID, data: TANCH) -> None:
        """Save anchor to memory."""
        self.__mem__[id] = data

    def remove(self, ids: ID | Iterable[ID]) -> None:
        """Remove anchor/s from memory."""
        if not isinstance(ids, Iterable):
            ids = [ids]

        for id in ids:
            self.__mem__.pop(id, None)
            self.__gc__.add(id)


@dataclass
class ShelfStorage(Memory[UUID, Anchor]):
    """Shelf Handler."""

    __shelf__: Shelf[Anchor] | None = None

    def __init__(self, session: str | None = None) -> None:
        """Initialize memory handler."""
        super().__init__()
        self.__shelf__ = open(session) if session else None  # noqa: SIM115

    def close(self) -> None:
        """Close memory handler."""
        if isinstance(self.__shelf__, Shelf):
            for id in self.__gc__:
                self.__shelf__.pop(str(id), None)
                self.__mem__.pop(id, None)

            self.sync(set(self.__mem__.values()))
            self.__shelf__.close()
        super().close()

    def sync(self, data: Anchor | Iterable[Anchor]) -> None:
        """Sync data to Shelf."""
        if isinstance(self.__shelf__, Shelf):
            if not isinstance(data, Iterable):
                data = [data]

            for d in data:
                _id = str(d.id)
                if d.architype and d.state.persistent:
                    if d.state.deleted is False:
                        d.state.deleted = True
                        self.__shelf__.pop(_id, None)
                    elif not d.state.connected:
                        d.state.connected = True
                        d.state.hash = hash(dumps(d))
                        self.__shelf__[_id] = d
                    elif (
                        isinstance(d, NodeAnchor)
                        and not isinstance(d.architype, Root)
                        and not d.edges
                    ):
                        d.state.deleted = True
                        self.__shelf__.pop(_id, None)
                    elif d.state.hash != (new_hash := hash(dumps(d))):
                        d.state.hash = new_hash
                        self.__shelf__[_id] = d

            self.__shelf__.sync()

    def find(
        self,
        ids: UUID | Iterable[UUID],
        filter: Callable[[Anchor], Anchor] | None = None,
    ) -> Generator[Anchor, None, None]:
        """Find anchors from datasource by ids with filter."""
        if not isinstance(ids, Iterable):
            ids = [ids]

        if isinstance(self.__shelf__, Shelf):
            for id in ids:
                anchor = self.__mem__.get(id)

                if (
                    not anchor
                    and id not in self.__gc__
                    and (_anchor := self.__shelf__.get(str(id)))
                ):
                    self.__mem__[id] = anchor = _anchor
                if anchor and (not filter or filter(anchor)):
                    yield anchor
        else:
            yield from super().find(ids, filter)
