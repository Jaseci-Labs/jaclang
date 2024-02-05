from os import getenv
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.exceptions import HTTPException

from jwt import decode, encode
from bcrypt import hashpw as _hashpw, gensalt
from passlib.context import CryptContext

from jaclang_fastapi.models import User
from jaclang_fastapi.memory import TokenMemory
from jaclang_fastapi.utils import logger, utc_now


TOKEN_SECRET = getenv("TOKEN_SECRET")
TOKEN_ALGORITHM = getenv("TOKEN_ALGORITHM")


def encrypt(data: dict) -> str:
    return encode(data, key=TOKEN_SECRET, algorithm=TOKEN_ALGORITHM)


def decrypt(token: str) -> dict:
    try:
        return decode(token, key=TOKEN_SECRET, algorithms=[TOKEN_ALGORITHM])
    except Exception:
        logger.exception("Token is invalid!")
        return None


def hashpw(password: str) -> bytes:
    return _hashpw(password.encode(), gensalt())


async def create_token(user: dict) -> str:
    user["expiration"] = utc_now(hours=int(getenv("TOKEN_TIMEOUT") or "12"))
    token = encrypt(user)
    if await TokenMemory.hset(key=token, data=True):
        return token
    raise HTTPException(500, "Token Creation Failed!")


async def authenticate(
    request: Request, Authorization: Annotated[str, Header()]
):  # noqa N803
    if Authorization and Authorization.lower().startswith("bearer"):
        token = Authorization[7:]
        decrypted = decrypt(token)
        if (
            decrypted
            and decrypted["expiration"] > utc_now()
            and await TokenMemory.hget(key=token)
        ):
            request.auth_user = await User.Collector.find_by_id(decrypted["id"])
            return

    raise HTTPException(status_code=401)


verify = CryptContext(schemes=["bcrypt"], deprecated="auto").verify
authenticator = [Depends(authenticate)]
