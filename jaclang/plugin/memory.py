"""Memory abstraction for jaseci plugin."""

from dataclasses import dataclass, field
from os import getenv
from shelve import Shelf, open
from typing import Callable, Generator, Literal, Optional, Union, overload
from uuid import UUID

from jaclang.core.construct import ObjectAnchor

IDS = Union[UUID, list[UUID]]
ENABLE_MANUAL_SAVE = getenv("ENABLE_MANUAL_SAVE") == "true"


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
                if str(d.id) not in self.__trash__:
                    self.__mem__[str(d.id)] = d
        elif str(data.id) not in self.__trash__:
            self.__mem__[str(data.id)] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Temporary."""
        if isinstance(data, list):
            for d in data:
                self.__mem__.pop(str(d.id), None)
                self.__trash__.add(str(d.id))
        else:
            self.__mem__.pop(str(data.id), None)
            self.__trash__.add(str(data.id))


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
        if isinstance(self.__shelf__, Shelf):
            for anchor in self.__mem__.values():
                if not anchor.persistent:
                    anchor.destroy()

            if not ENABLE_MANUAL_SAVE:
                for id in self.__trash__:
                    self.__shelf__.pop(id, None)

                for anchor in set(self.__mem__.values()):
                    anchor.save()
            self.__shelf__.sync()

        super().close()

    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[ObjectAnchor], ObjectAnchor]] = None,
        extended: Optional[bool] = None,
    ) -> Generator[ObjectAnchor, None, None]:
        """Temporary."""
        objs = super().find(ids, filter, True)

        if isinstance(self.__shelf__, Shelf):
            for obj in objs:
                if isinstance(obj, UUID):
                    if str(obj) not in self.__trash__ and (
                        anchor := self.__shelf__.get(str(obj))
                    ):
                        if architype := anchor.architype:
                            architype._jac_ = anchor
                        self.__mem__[str(anchor.id)] = anchor
                        if not filter or filter(anchor):
                            yield anchor
                else:
                    yield obj
        else:
            for obj in objs:
                if isinstance(obj, ObjectAnchor):
                    yield obj

    def set(
        self, data: Union[ObjectAnchor, list[ObjectAnchor]], mem_only: bool = False
    ) -> None:
        """Temporary."""
        super().set(data)

        if not mem_only and isinstance(self.__shelf__, Shelf):
            if isinstance(data, list):
                for d in data:
                    self.__shelf__[str(d.id)] = d
            else:
                self.__shelf__[str(data.id)] = data

    def remove(self, data: Union[ObjectAnchor, list[ObjectAnchor]]) -> None:
        """Temporary."""
        super().remove(data)
        if isinstance(self.__shelf__, Shelf) and ENABLE_MANUAL_SAVE:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__.pop(str(d.id), None)
            else:
                self.__shelf__.pop(str(data.id), None)
