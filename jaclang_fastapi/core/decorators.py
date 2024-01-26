"""Not Available Yet."""

from functools import wraps
from typing import Callable

from fastapi.responses import Response

from jaclang_fastapi.core import app


def fapi(method: str, path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""
    _m = getattr(app, method)

    def outter_wrapper(func: Callable) -> Callable:
        @_m(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def jget(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.get(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def jpost(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.post(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def jput(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.put(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def jdelete(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.delete(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def jhead(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.head(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def jtrace(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.trace(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper


def joptions(path: str, *args, **kwargs) -> Callable:  # noqa: ANN002, ANN003
    """Not Available Yet."""

    def outter_wrapper(func: Callable) -> Callable:
        @app.options(path, *args, **kwargs)
        @wraps(func)
        def inner_wrapper(*args, **kwargs) -> Response:  # noqa: ANN002, ANN003
            return func(*args, **kwargs)

        return inner_wrapper

    return outter_wrapper
