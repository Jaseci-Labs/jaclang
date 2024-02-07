from os import getenv

from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer

from jwt import decode, encode
from passlib.context import CryptContext

from jaclang_fastapi.plugins import Root
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


async def create_token(user: dict) -> str:
    user["expiration"] = utc_now(hours=int(getenv("TOKEN_TIMEOUT") or "12"))
    token = encrypt(user)
    if await TokenMemory.hset(key=token, data=True):
        return token
    raise HTTPException(500, "Token Creation Failed!")


async def authenticate(request: Request):  # noqa N803
    authorization = request.headers.get("Authorization")
    if authorization and authorization.lower().startswith("bearer"):
        token = authorization[7:]
        decrypted = decrypt(token)
        if (
            decrypted
            and decrypted["expiration"] > utc_now()
            and await TokenMemory.hget(key=token)
        ):
            request.auth_user = await User.model().Collection.find_by_id(
                decrypted["id"]
            )
            request.user_root = await Root.Collection.find_by_id(
                request.auth_user.root_id
            )
            return

    raise HTTPException(status_code=401)


verify = CryptContext(schemes=["bcrypt"], deprecated="auto").verify
authenticator = [Depends(HTTPBearer()), Depends(authenticate)]
