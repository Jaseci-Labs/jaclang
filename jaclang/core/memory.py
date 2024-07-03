"""Memory abstraction for jaseci plugin."""

from copy import deepcopy
from dataclasses import dataclass, field
from shelve import Shelf, open
from typing import Any, Callable, Generator, Optional, Union, cast
from uuid import UUID

from .architype import (
    Architype,
    EdgeAnchor,
    EdgeArchitype,
    MANUAL_SAVE,
    NodeAnchor,
    NodeArchitype,
    ObjectAnchor,
    ObjectType,
    Permission,
    WalkerAnchor,
    WalkerArchitype,
)

IDS = Union[UUID, list[UUID]]


@dataclass
class Memory:
    """Generic Memory Handler."""

    __mem__: dict[str, ObjectAnchor] = field(default_factory=dict)
    __gc__: set[str] = field(default_factory=set)

    def close(self) -> None:
        """Close memory handler."""
        self.__mem__.clear()
        self.__gc__.clear()

    def __del__(self) -> None:
        """On garbage collection cleanup."""
        self.close()

    def find(
        self, ids: IDS, filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None
    ) -> Generator[ObjectAnchor, None, None]:
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
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None,
    ) -> Optional[ObjectAnchor]:
        """Find one anchor from memory by ids with filter."""
        return next(self.find(ids, filter), None)

    def set(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Save anchor/s to memory."""
        if isinstance(data, list):
            for d in data:
                if str(d.id) not in self.__gc__:
                    self.__mem__[str(d.id)] = d
        elif str(data.id) not in self.__gc__:
            self.__mem__[str(data.id)] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Remove anchor/s from memory."""
        if isinstance(data, list):
            for d in data:
                self.__mem__.pop(str(d.id), None)
                self.__gc__.add(str(d.id))
        else:
            self.__mem__.pop(str(data.id), None)
            self.__gc__.add(str(data.id))


@dataclass
class ShelfMemory(Memory):
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
                if not anchor.persistent:
                    anchor.destroy()
                elif not MANUAL_SAVE:
                    for id in self.__gc__:
                        self.__shelf__.pop(id, None)
                    anchor.save()
            self.__shelf__.sync()

        super().close()

    def find(
        self, ids: IDS, filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None
    ) -> Generator[ObjectAnchor, None, None]:
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

    def set(
        self, data: Union[ObjectAnchor, list[ObjectAnchor]], mem_only: bool = False
    ) -> None:
        """Save anchor/s to datasource."""
        super().set(data)

        if not mem_only and isinstance(self.__shelf__, Shelf):
            for d in data if isinstance(data, list) else [data]:
                _id = str(d.id)
                json = d.serialize()
                if _id not in self.__shelf__:
                    self.__shelf__[_id] = json
                else:
                    if d.current_access_level > 0 and isinstance(d, NodeAnchor):
                        self.__shelf__[_id]["edges"] = json["edges"]
                    if d.current_access_level > 1:
                        self.__shelf__[_id]["architype"] = json["architype"]

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Remove anchor/s from datasource."""
        super().remove(data)
        if isinstance(self.__shelf__, Shelf) and MANUAL_SAVE:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__.pop(str(d.id), None)
            else:
                self.__shelf__.pop(str(data.id), None)

    def get(self, anchor: dict[str, Any]) -> ObjectAnchor:
        """Get Anchor Instance."""
        name = cast(str, anchor.get("name"))
        architype = anchor.pop("architype")
        access = Permission.deserialize(anchor.pop("access"))

        match ObjectType(anchor.pop("type")):
            case ObjectType.node:
                nanch = NodeAnchor(
                    edges=[
                        e for edge in anchor.pop("edges") if (e := EdgeAnchor.ref(edge))
                    ],
                    access=access,
                    **anchor,
                )
                nanch.architype = NodeArchitype.get(name or "Root")(
                    _jac_=nanch, **architype
                )
                return nanch
            case ObjectType.edge:
                eanch = EdgeAnchor(
                    source=NodeAnchor.ref(anchor.pop("source")),
                    target=NodeAnchor.ref(anchor.pop("target")),
                    access=access,
                    **anchor,
                )
                eanch.architype = EdgeArchitype.get(name or "GenericEdge")(
                    _jac_=eanch, **architype
                )
                return eanch
            case ObjectType.walker:
                wanch = WalkerAnchor(access=access, **anchor)
                wanch.architype = WalkerArchitype.get(name)(_jac_=wanch, **architype)
                return wanch
            case _:
                oanch = ObjectAnchor(access=access, **anchor)
                oanch.architype = Architype(_jac_=oanch)
                return oanch
