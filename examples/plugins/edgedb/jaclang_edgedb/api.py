"""JacLang FastAPI Core."""

from typing import Any
from annotated_types import T
from uvicorn.config import LOGGING_CONFIG

from fastapi import FastAPI as _FaststAPI
from jaclang_edgedb.walkerapi import DefaultSpecs

from uvicorn import run as _run


class FastAPI:
    """FastAPI Handler."""

    __app__ = None

    @classmethod
    def get(cls) -> _FaststAPI:
        """Get or Create new instance of FastAPI."""
        if not isinstance(cls.__app__, _FaststAPI):
            cls.__app__ = _FaststAPI()

            # from ..routers import user_router
            from .walkerapi import router

            cls.__app__.include_router(router)

        return cls.__app__

    @classmethod
    def start(
        cls, host: str = "0.0.0.0", port: int = 8000, **kwargs: dict[str, Any]
    ) -> None:
        """Run FastAPI Handler via Uvicorn."""
        _run(cls.get(), loop="asyncio", host=host, port=port, **kwargs)


def api_exclude(cls: type) -> None:
    """Get DefaultSpecs."""
    if hasattr(cls, "Specs"):
        cls.Specs.exclude = True
        print(cls.Specs.exclude)
