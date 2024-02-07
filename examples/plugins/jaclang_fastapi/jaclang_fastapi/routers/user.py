from bson import ObjectId

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from jaclang_fastapi.models import User
from jaclang_fastapi.models.ephemerals import UserRequest
from jaclang_fastapi.securities import create_token, verify
from jaclang_fastapi.plugins import Root
from jaclang_fastapi.utils import utc_now, logger

router = APIRouter(prefix="/user", tags=["user"])

User = User.model()


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(req: User.register_type()):
    async with await Root.Collection.get_session() as session:
        async with session.start_transaction():
            try:
                root_id = await Root.Collection.insert_one(
                    {"date_created": utc_now()}, session=session
                )

                req_obf = req.obfuscate()
                req_obf["root_id"] = root_id
                result = await User.Collection.insert_one(req_obf, session=session)

                await session.commit_transaction()
            except Exception as e:
                logger.exception("Error commiting user registration!")
                result = None

                await session.abort_transaction()

    if result:
        return ORJSONResponse({"message": "Successfully Registered!"}, 201)
    else:
        return ORJSONResponse({"message": "Registration Failed!"}, 409)


@router.post("/login")
async def root(req: UserRequest):
    user: User = await User.Collection.find_by_email(req.email)
    if not user or not verify(req.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid Email/Password!")
    user_json = user.json()
    token = await create_token(user_json)

    return ORJSONResponse(content={"token": token, "user": user_json})
