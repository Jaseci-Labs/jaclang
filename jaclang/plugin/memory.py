"""Memory abstraction for jaseci plugin."""

from dataclasses import dataclass, field
from shelve import Shelf, open
from typing import Callable, Generator, Literal, Optional, Union, overload
from uuid import UUID

from jaclang.core.construct import ObjectAnchor

IDS = Union[UUID, list[UUID]]


@dataclass
class Memory:
    """Generic Memory Handler."""

    __mem__: dict[str, ObjectAnchor] = field(default_factory=dict)

    def close(self) -> None:
        """Close memory handler."""
        self.__mem__.clear()

    def __del__(self) -> None:
        """On garbage collection cleanup."""
        self.close()

    @overload
    def find(
        self, ids: IDS, filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]]
    ) -> Generator[ObjectAnchor, None, None]:
        pass

    @overload
    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]],
        extended: Literal[True],
    ) -> Generator[Union[UUID, ObjectAnchor], None, None]:
        pass

    @overload
    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]],
        extended: Literal[False],
    ) -> Generator[ObjectAnchor, None, None]:
        pass

    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None,
        extended: Optional[bool] = False,
    ) -> Generator[Union[UUID, ObjectAnchor], None, None]:
        """Temporary."""
        if not isinstance(ids, list):
            ids = [ids]

        for id in ids:
            if (anchor := self.__mem__.get(str(id))) and (not filter or filter(anchor)):
                yield anchor
            elif extended:
                yield id

    def find_one(
        self,
        ids: IDS,
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None,
    ) -> Optional[ObjectAnchor]:
        """Temporary."""
        return next(self.find(ids, filter), None)

    def set(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Temporary."""
        if isinstance(data, list):
            for d in data:
                self.__mem__[d.ref_id] = d
        else:
            self.__mem__[data.ref_id] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Temporary."""
        if isinstance(data, list):
            for d in data:
                self.__mem__.pop(d.ref_id, None)
        else:
            self.__mem__.pop(data.ref_id, None)


@dataclass
class ShelfMemory(Memory):
    """Generic Memory Handler."""

    __shelf__: Optional[Shelf[ObjectAnchor]] = None

    def __init__(self, session: Optional[str] = None) -> None:
        """Initialize memory handler."""
        super().__init__()
        self.__shelf__ = open(session) if session else None  # noqa: SIM115

    def close(self) -> None:
        """Close memory handler."""
        super().close()
        if self.__shelf__:
            self.__shelf__.close()

    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None,
        extended: Optional[bool] = None,
    ) -> Generator[ObjectAnchor, None, None]:
        """Temporary."""
        objs = super().find(ids, filter, True)

        if self.__shelf__:
            for obj in objs:
                if isinstance(obj, UUID):
                    if anchor := self.__shelf__.get(str(obj)):
                        self.__mem__[anchor.ref_id] = anchor
                        if not filter or filter(anchor):
                            yield anchor
                else:
                    yield obj
        else:
            for obj in objs:
                if isinstance(obj, ObjectAnchor):
                    yield obj

    def set(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Temporary."""
        super().set(data)

        if self.__shelf__:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__[str(d.id)] = d
            else:
                self.__shelf__[str(data.id)] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Temporary."""
        super().remove(data)

        if self.__shelf__:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__.pop(str(d.id), None)
            else:
                self.__shelf__.pop(str(data.id), None)
