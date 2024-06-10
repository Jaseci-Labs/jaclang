"""Memory abstraction for jaseci plugin."""

from shelve import Shelf, open
from types import TracebackType
from typing import (
    Callable,
    Generic,
    MutableMapping,
    Optional,
    Type,
    TypeVar,
    Union,
)

from jaclang.core.construct import Architype


T = TypeVar("T", bound="Memory")
ID = TypeVar("ID")


class Memory(Generic[ID]):
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

    def open(self: T) -> T:
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

    def __enter__(self: T) -> T:
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

    def find(self, filter: tuple[Union[ID, list[ID]], Callable]) -> list[Architype]:
        """Temporary."""
        return []
