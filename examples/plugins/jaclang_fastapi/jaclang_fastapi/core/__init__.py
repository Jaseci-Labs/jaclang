from fastapi import FastAPI as _FaststAPI

from uvicorn import run as _run


class FastAPI:
    __app__ = None

    @classmethod
    def get(cls) -> _FaststAPI:
        if not isinstance(cls.__app__, _FaststAPI):
            cls.__app__ = _FaststAPI()

            from jaclang_fastapi.routers import user_router
            from jaclang_fastapi.plugins import walker_router

            for router in [user_router, walker_router]:
                cls.__app__.include_router(router)

        return cls.__app__

    @classmethod
    def start(
        cls, host: str = "0.0.0.0", port: int = 8000, **kwargs
    ) -> None:  # noqa: ANN003
        """Not Available Yet."""
        _run(cls.get(), host=host, port=port, **kwargs)
