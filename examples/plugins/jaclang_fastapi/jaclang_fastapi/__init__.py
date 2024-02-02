from fastapi import FastAPI as _FaststAPI

from typing import Callable, TypeVar, Union

from uvicorn import run as _run

T = TypeVar("T")


class FastAPI:
    __app__ = None

    @classmethod
    def get(cls) -> _FaststAPI:
        if not isinstance(cls.__app__, _FaststAPI):
            cls.__app__ = _FaststAPI()
            cls.walker_get = cls.__app__.get
            cls.walker_post = cls.__app__.post
            cls.walker_put = cls.__app__.put
            cls.walker_patch = cls.__app__.patch
            cls.walker_delete = cls.__app__.delete
            cls.walker_head = cls.__app__.head
            cls.walker_options = cls.__app__.options
            cls.walker_trace = cls.__app__.trace

        return cls.__app__

    @classmethod
    def start(
        cls, host: str = "0.0.0.0", port: int = 8000, **kwargs
    ) -> None:  # noqa: ANN003
        """Not Available Yet."""
        _run(cls.get(), host=host, port=port, **kwargs)


def options(
    path: str = "", allowed_methods: list[str] = [], as_query: Union[str, list] = []
) -> Callable:
    def wrapper(func: T) -> T:
        func.__options__ = {
            "path": path,
            "allowed_methods": allowed_methods,
            "as_query": as_query,
        }
        return func

    return wrapper


FastAPI.post = FastAPI.get().post
start = FastAPI.start

__all__ = ["FastAPI", "options", "start"]
