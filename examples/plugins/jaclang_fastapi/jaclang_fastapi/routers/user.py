from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from jaclang_fastapi.models import User
from jaclang_fastapi.models.ephemerals import UserRequest
from jaclang_fastapi.securities import create_token, verify


router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(req: User.register_type()):
    result = await User.Collector.insert_one(req.obfuscate())

    if result:
        return ORJSONResponse({"message": "Successfully Registered!"}, 201)
    else:
        return ORJSONResponse({"message": "Registration Failed!"}, 409)


@router.post("/login")
async def root(req: UserRequest):
    user: User = await User.Collector.find_by_email(req.email)
    if not user or not verify(req.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid Email/Password!")

    token = await create_token(user.json())

    return ORJSONResponse(content={"token": token})
