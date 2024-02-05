from .core import FastAPI

from dotenv import load_dotenv

load_dotenv()

start = FastAPI.start

__all__ = ["FastAPI", "start"]

FastAPI.get()
