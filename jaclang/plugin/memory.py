"""Memory abstraction for jaseci plugin."""

from shelve import Shelf, open
from types import TracebackType
from typing import (
    Callable,
    Generator,
    MutableMapping,
    Optional,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from jaclang.core.construct import Architype


M = TypeVar("M", bound="Memory")
A = TypeVar("A", bound=Architype)
IDS = Union[UUID, list[UUID]]


class Memory:
    """Generic Memory Handler."""

    ##################################################
    #     NO INTIALIZATION JUST FOR TYPE HINTING     #
    ##################################################

    __ses__: Optional[str]
    __mem__: MutableMapping[str, Architype]

    # ---------------------------------------------- #

    def __init__(self, session: Optional[str] = None) -> None:
        """Initialize memory handler."""
        self.__ses__ = session

    def open(self: M) -> M:
        """Open memory handler."""
        if self.__ses__:
            self.__mem__ = open(self.__ses__)  # noqa: SIM115
        else:
            self.__mem__ = {}

        return self

    def close(self) -> None:
        """Close memory handler."""
        if isinstance(self.__mem__, Shelf):
            self.__mem__.close()
        else:
            self.__mem__.clear()

    def __enter__(self: M) -> M:
        """Open memory handler via context handler."""
        return self.open()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Close memory handler via context handler."""
        self.close()

    def __del__(self) -> None:
        """On garbage collection cleanup."""
        self.close()

    def find(
        self,
        ids: IDS,
        filter: Optional[Callable[[Architype], Architype]],
    ) -> Generator[Architype, None, None]:
        """Temporary."""
        if not isinstance(ids, list):
            ids = [ids]

        return (
            filter(obj) if filter else obj
            for id in ids
            if (obj := self.__mem__.get(str(id)))
        )

    def find_one(
        self, ids: IDS, filter: Optional[Callable[[Architype], Architype]]
    ) -> Architype:
        """Temporary."""
        return next(self.find(ids, filter))

    def set(self, data: Union[Architype, list[Architype]]) -> None:
        """Temporary."""
        if not isinstance(data, list):
            data = [data]

        for d in data:
            self.__mem__[str(d._jac_.id)] = d

    def remove(self, data: Union[Architype, list[Architype]]) -> None:
        """Temporary."""
        if not isinstance(data, list):
            data = [data]

        for d in data:
            self.__mem__.pop(str(d._jac_.id))
