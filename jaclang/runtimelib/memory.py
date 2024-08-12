"""Memory abstraction for jaseci plugin."""

from copy import deepcopy
from dataclasses import dataclass, field
from os import getenv
from shelve import Shelf, open
from typing import Any, Callable, Generator, Iterable, Optional, Union, cast
from uuid import UUID

from .architype import (
    AccessLevel,
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
    Root,
    WalkerAnchor,
    WalkerAnchorState,
    WalkerArchitype,
    to_dataclass,
)

DISABLE_AUTO_CLEANUP = getenv("DISABLE_AUTO_CLEANUP") == "true"
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
            for id in self.__gc__:
                self.__shelf__.pop(id, None)
                self.__mem__.pop(id, None)

            if not MANUAL_SAVE:
                self.sync(set(self.__mem__.values()))
            self.__shelf__.close()
        super().close()

    def sync(self, data: Union[Anchor, Iterable[Anchor]]) -> None:
        """Sync data to Shelf."""
        if isinstance(self.__shelf__, Shelf):
            if not isinstance(data, Iterable):
                data = [data]

            for d in data:
                _id = str(d.id)
                if d.architype and d.state.persistent:
                    if d.state.deleted is False:
                        self.__shelf__.pop(_id, None)
                    elif not d.state.connected:
                        self.__shelf__[_id] = d.serialize()
                    elif (
                        not DISABLE_AUTO_CLEANUP
                        and isinstance(d, NodeAnchor)
                        and not isinstance(d.architype, Root)
                        and not d.edges
                    ):
                        self.__shelf__.pop(_id, None)
                    elif d.state.hash != d.data_hash():
                        new_data = d.serialize()
                        ref_data = self.__shelf__[_id]

                        if (
                            isinstance(d, NodeAnchor)
                            and new_data["edges"] != ref_data["edges"]
                            and d.state.current_access_level > AccessLevel.READ
                        ):
                            ref_data["edges"] = new_data["edges"]

                        if d.state.current_access_level > AccessLevel.CONNECT:
                            if new_data["access"] != ref_data["access"]:
                                ref_data["access"] = new_data["access"]
                            if new_data["architype"] != ref_data["architype"]:
                                ref_data["architype"] = new_data["architype"]

                        self.__shelf__[_id] = ref_data

            self.__shelf__.sync()

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

    def remove(self, data: Union[Anchor, list[Anchor]], from_db: bool = False) -> None:
        """Remove anchor/s from datasource."""
        super().remove(data)
        if isinstance(self.__shelf__, Shelf) and from_db:
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
                nanch.architype = to_dataclass(narch, architype, __jac__=nanch)
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
                eanch.architype = to_dataclass(earch, architype, __jac__=eanch)
                eanch.sync_hash()
                return eanch
            case AnchorType.walker:
                wanch = WalkerAnchor(
                    access=access, state=WalkerAnchorState(connected=True), **anchor
                )
                warch = WalkerArchitype.__get_class__(name)
                wanch.architype = to_dataclass(warch, architype, __jac__=wanch)
                wanch.sync_hash()
                return wanch
            case _:
                oanch = Anchor(
                    access=access, state=AnchorState(connected=True), **anchor
                )
                oanch.architype = Architype(__jac__=oanch)
                oanch.sync_hash()
                return oanch
