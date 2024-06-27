"""Memory abstraction for jaseci plugin."""

from dataclasses import dataclass, field
from shelve import Shelf, open
from typing import Callable, Generator, Optional, Union
from uuid import UUID

from .architype import MANUAL_SAVE, ObjectAnchor

IDS = Union[UUID, list[UUID]]


@dataclass
class Memory:
    """Generic Memory Handler."""

    __mem__: dict[str, ObjectAnchor] = field(default_factory=dict)
    __trash__: set[str] = field(default_factory=set)

    def close(self) -> None:
        """Close memory handler."""
        self.__mem__.clear()
        self.__trash__.clear()

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
                if str(d.id) not in self.__trash__:
                    self.__mem__[str(d.id)] = d
        elif str(data.id) not in self.__trash__:
            self.__mem__[str(data.id)] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Remove anchor/s from memory."""
        if isinstance(data, list):
            for d in data:
                self.__mem__.pop(str(d.id), None)
                self.__trash__.add(str(d.id))
        else:
            self.__mem__.pop(str(data.id), None)
            self.__trash__.add(str(data.id))


@dataclass
class ShelfMemory(Memory):
    """Shelf Handler."""

    __shelf__: Optional[Shelf[ObjectAnchor]] = None

    def __init__(self, session: Optional[str] = None) -> None:
        """Initialize memory handler."""
        super().__init__()
        self.__shelf__ = open(session) if session else None  # noqa: SIM115

    def close(self) -> None:
        """Close memory handler."""
        if isinstance(self.__shelf__, Shelf):
            for anchor in self.__mem__.values():
                if not anchor.persistent:
                    anchor.destroy()

            if not MANUAL_SAVE:
                for id in self.__trash__:
                    self.__shelf__.pop(id, None)

                for anchor in set(self.__mem__.values()):
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
                    and _id not in self.__trash__
                    and (anchor := self.__shelf__.get(_id))
                    and (architype := anchor.architype)
                ):
                    self.__mem__[_id] = architype._jac_ = anchor

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
            if isinstance(data, list):
                for d in data:
                    self.__shelf__[str(d.id)] = d
            else:
                self.__shelf__[str(data.id)] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Remove anchor/s from datasource."""
        super().remove(data)
        if isinstance(self.__shelf__, Shelf) and MANUAL_SAVE:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__.pop(str(d.id), None)
            else:
                self.__shelf__.pop(str(data.id), None)
