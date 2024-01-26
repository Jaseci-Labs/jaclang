"""Not Available Yet."""

from jaclang_fastapi import app

from uvicorn import run


def start(host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:  # noqa: ANN003
    """Not Available Yet."""
    run(app, host=host, port=port, **kwargs)
