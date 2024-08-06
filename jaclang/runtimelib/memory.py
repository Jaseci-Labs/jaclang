"""Memory abstraction for jaseci plugin."""

from copy import deepcopy
from dataclasses import dataclass, field
from shelve import Shelf, open
from typing import Any, Callable, Generator, Optional, Union, cast
from uuid import UUID

from .architype import (
    Anchor,
    AnchorState,
    AnchorType,
    Architype,
    EdgeAnchor,
    EdgeArchitype,
    MANUAL_SAVE,
    NodeAnchor,
    NodeArchitype,
    Permission,
    WalkerAnchor,
    WalkerAnchorState,
    WalkerArchitype,
    populate_dataclasses,
)

IDS = Union[UUID, list[UUID]]


@dataclass
class Memory:
    """Generic Memory Handler."""

    __mem__: dict[str, Anchor] = field(default_factory=dict)
    __gc__: set[str] = field(default_factory=set)

    def close(self) -> None:
        """Close memory handler."""
        self.__mem__.clear()
        self.__gc__.clear()

    def find(
        self, ids: IDS, filter: Optional[Callable[[Anchor], Anchor]] = None
    ) -> Generator[Anchor, None, None]:
        """Find anchors from memory by ids with filter."""
        if not isinstance(ids, list):
            ids = [ids]

        return (
            anchor
            for id in ids
            if (anchor := self.__mem__.get(str(id))) and (not filter or filter(anchor))
        )

    def find_one(
        self,
        ids: IDS,
        filter: Optional[Callable[[Anchor], Anchor]] = None,
    ) -> Optional[Anchor]:
        """Find one anchor from memory by ids with filter."""
        return next(self.find(ids, filter), None)

    def set(self, data: Union[Anchor, list[Anchor]]) -> None:
        """Save anchor/s to memory."""
        if isinstance(data, list):
            for d in data:
                if str(d.id) not in self.__gc__:
                    self.__mem__[str(d.id)] = d
        elif str(data.id) not in self.__gc__:
            self.__mem__[str(data.id)] = data

    def remove(self, data: Union[Anchor, list[Anchor]]) -> None:
        """Remove anchor/s from memory."""
        if isinstance(data, list):
            for d in data:
                self.__mem__.pop(str(d.id), None)
                self.__gc__.add(str(d.id))
        else:
            self.__mem__.pop(str(data.id), None)
            self.__gc__.add(str(data.id))


@dataclass
class ShelfStorage(Memory):
    """Shelf Handler."""

    __shelf__: Optional[Shelf[dict[str, object]]] = None

    def __init__(self, session: Optional[str] = None) -> None:
        """Initialize memory handler."""
        super().__init__()
        self.__shelf__ = open(session) if session else None  # noqa: SIM115

    def close(self) -> None:
        """Close memory handler."""
        if isinstance(self.__shelf__, Shelf):
            for anchor in set(self.__mem__.values()):
                if not anchor.state.persistent:
                    anchor.destroy()
                elif not MANUAL_SAVE:
                    anchor.save()
            for id in self.__gc__:
                self.__shelf__.pop(id, None)
            self.__shelf__.sync()

        super().close()

    def find(
        self, ids: IDS, filter: Optional[Callable[[Anchor], Anchor]] = None
    ) -> Generator[Anchor, None, None]:
        """Find anchors from datasource by ids with filter."""
        if not isinstance(ids, list):
            ids = [ids]

        if isinstance(self.__shelf__, Shelf):
            for id in ids:
                _id = str(id)
                anchor = self.__mem__.get(_id)

                if (
                    not anchor
                    and _id not in self.__gc__
                    and (_anchor := self.__shelf__.get(_id))
                ):
                    self.__mem__[_id] = anchor = self.get(deepcopy(_anchor))
                if anchor and (not filter or filter(anchor)):
                    yield anchor
        else:
            yield from super().find(ids, filter)

    def set(self, data: Union[Anchor, list[Anchor]], mem_only: bool = False) -> None:
        """Save anchor/s to datasource."""
        super().set(data)

        if not mem_only and isinstance(self.__shelf__, Shelf):
            for d in data if isinstance(data, list) else [data]:
                self.__shelf__[str(d.id)] = d.serialize()

    def remove(self, data: Union[Anchor, list[Anchor]]) -> None:
        """Remove anchor/s from datasource."""
        super().remove(data)
        if isinstance(self.__shelf__, Shelf) and MANUAL_SAVE:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__.pop(str(d.id), None)
            else:
                self.__shelf__.pop(str(data.id), None)

    def get(self, anchor: dict[str, Any]) -> Anchor:
        """Get Anchor Instance."""
        name = cast(str, anchor.get("name"))
        architype = anchor.pop("architype")
        access = Permission.deserialize(anchor.pop("access"))
        match AnchorType(anchor.pop("type")):
            case AnchorType.node:
                nanch = NodeAnchor(
                    edges=[
                        e for edge in anchor.pop("edges") if (e := EdgeAnchor.ref(edge))
                    ],
                    access=access,
                    state=AnchorState(connected=True),
                    **anchor,
                )
                narch = NodeArchitype.__get_class__(name or "Root")
                nanch.architype = narch(
                    __jac__=nanch, **populate_dataclasses(narch, architype)
                )
                nanch.sync_hash()
                return nanch
            case AnchorType.edge:
                eanch = EdgeAnchor(
                    source=NodeAnchor.ref(anchor.pop("source")),
                    target=NodeAnchor.ref(anchor.pop("target")),
                    access=access,
                    state=AnchorState(connected=True),
                    **anchor,
                )
                earch = EdgeArchitype.__get_class__(name or "GenericEdge")
                eanch.architype = earch(
                    __jac__=eanch, **populate_dataclasses(earch, architype)
                )
                eanch.sync_hash()
                return eanch
            case AnchorType.walker:
                wanch = WalkerAnchor(
                    access=access, state=WalkerAnchorState(connected=True), **anchor
                )
                warch = WalkerArchitype.__get_class__(name)
                wanch.architype = warch(
                    __jac__=wanch, **populate_dataclasses(warch, architype)
                )
                wanch.sync_hash()
                return wanch
            case _:
                oanch = Anchor(
                    access=access, state=AnchorState(connected=True), **anchor
                )
                oanch.architype = Architype(__jac__=oanch)
                oanch.sync_hash()
                return oanch
