"""JacLang FastAPI."""

from dotenv import load_dotenv

from .core import FastAPI


load_dotenv()

start = FastAPI.start

__all__ = ["FastAPI", "start"]
