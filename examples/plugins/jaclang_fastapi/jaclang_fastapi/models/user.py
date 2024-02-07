from pydantic import create_model

from bcrypt import hashpw, gensalt

from pydantic import BaseModel, EmailStr
from pydantic.fields import FieldInfo

from jaclang_fastapi.collections.user import UserCollection

NULL_BYTES = bytes()


class UserCommon(BaseModel):
    def json(self):
        return self.model_dump(exclude={"password"})

    def obfuscate(self):
        data = self.json()
        if isinstance(self.password, str):
            data["password"] = hashpw(self.password.encode(), gensalt())
        return data


class User(UserCommon):
    id: str
    email: EmailStr
    password: bytes

    class Collection(UserCollection):
        @classmethod
        def __document__(cls, doc) -> "User":
            return User.model()(
                id=str(doc.pop("_id")),
                email=doc.pop("email"),
                password=doc.pop("password", None) or NULL_BYTES,
                **doc,
            )

        @classmethod
        def __documents__(cls, docs) -> list["User"]:
            return [
                User.model()(
                    id=str(doc.get("_id")),
                    email=doc.get("email"),
                    password=doc.get("password") or NULL_BYTES,
                    **doc,
                )
                for doc in docs
            ]

    @staticmethod
    def model() -> type["User"]:
        if subs := __class__.__subclasses__():
            return subs[-1]
        return __class__

    @staticmethod
    def register_type() -> type:
        user_model = {}
        fields: dict[str, FieldInfo] = __class__.model().model_fields
        for key, val in fields.items():
            consts = [val.annotation]
            if callable(val.default_factory):
                consts.append(val.default_factory())
            else:
                consts.append(...)
            user_model[key] = tuple(consts)

        user_model["password"] = (str, ...)
        user_model.pop("id", None)

        return create_model(f"UserRegister", __base__=UserCommon, **user_model)
