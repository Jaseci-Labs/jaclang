"""Memory abstraction for jaseci plugin."""

from dataclasses import dataclass, field
from shelve import Shelf, open
from typing import Callable, Generator, Literal, Optional, TypeVar, Union, overload
from uuid import UUID

from jaclang.core.construct import Architype


M = TypeVar("M", bound="Memory")
A = TypeVar("A", bound=Architype)
ID = Union[str, UUID]
IDS = Union[ID, list[ID]]


@dataclass
class Memory:
    """Generic Memory Handler."""

    __mem__: dict[str, Architype] = field(default_factory=dict)

    def close(self) -> None:
        """Close memory handler."""
        self.__mem__.clear()

    def __del__(self) -> None:
        """On garbage collection cleanup."""
        self.close()

    @overload
    def find(
        self, ids: IDS, filter: Optional[Callable[[Architype], Architype]]
    ) -> Generator[Architype, None, None]:
        pass

    @overload
    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[Architype], Architype]],
        extended: Literal[True],
    ) -> Generator[Union[UUID, Architype], None, None]:
        pass

    @overload
    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[Architype], Architype]],
        extended: Literal[False],
    ) -> Generator[Architype, None, None]:
        pass

    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[Architype], Architype]] = None,
        extended: Optional[bool] = False,
    ) -> Generator[Union[UUID, Architype], None, None]:
        """Temporary."""
        if not isinstance(ids, list):
            ids = [ids]

        for id in ids:
            if (obj := self.__mem__.get(str(id))) and (not filter or filter(obj)):
                yield obj
            elif extended:
                yield UUID(id) if isinstance(id, str) else id

    def find_one(
        self,
        ids: IDS,
        filter: Optional[Callable[[Architype], Architype]] = None,
    ) -> Optional[Architype]:
        """Temporary."""
        return next(self.find(ids, filter), None)

    def set(self, data: Union[Architype, list[Architype]]) -> None:
        """Temporary."""
        if isinstance(data, list):
            for d in data:
                self.__mem__[str(d._jac_.id)] = d
        else:
            self.__mem__[str(data._jac_.id)] = data

    def remove(self, data: Union[Architype, list[Architype]]) -> None:
        """Temporary."""
        if isinstance(data, list):
            for d in data:
                self.__mem__.pop(str(d._jac_.id), None)
        else:
            self.__mem__.pop(str(data._jac_.id), None)


@dataclass
class ShelfMemory(Memory):
    """Generic Memory Handler."""

    __shelf__: Optional[Shelf[Architype]] = None

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
        filter: Optional[Callable[[Architype], Architype]],
        extended: Optional[bool] = None,
    ) -> Generator[Architype, None, None]:
        """Temporary."""
        objs = super().find(ids, filter, True)

        if self.__shelf__:
            for obj in objs:
                if isinstance(obj, UUID):
                    if arch := self.__shelf__.get(str(obj)):
                        super().set(arch)
                        if not filter or filter(arch):
                            yield arch
                else:
                    yield obj
        else:
            for obj in objs:
                if isinstance(obj, Architype):
                    yield obj

    def set(self, data: Union[Architype, list[Architype]]) -> None:
        """Temporary."""
        super().set(data)

        if self.__shelf__:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__[str(d._jac_.id)] = d
            else:
                self.__shelf__[str(data._jac_.id)] = data

    def remove(self, data: Union[Architype, list[Architype]]) -> None:
        """Temporary."""
        super().remove(data)

        if self.__shelf__:
            if isinstance(data, list):
                for d in data:
                    self.__shelf__.pop(str(d._jac_.id), None)
            else:
                self.__shelf__.pop(str(data._jac_.id), None)
