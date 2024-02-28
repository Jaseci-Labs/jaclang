"""User Models."""

from bcrypt import gensalt, hashpw

from pydantic import BaseModel, EmailStr, create_model
from pydantic.fields import FieldInfo

from ..collections.user import UserCollection

NULL_BYTES = bytes()


class UserCommon(BaseModel):
    """User Common Functionalities."""

    def json(self) -> dict:
        """Return BaseModel.model_dump excluding the password field."""
        return self.model_dump(exclude={"password"})

    def obfuscate(self) -> dict:
        """Return BaseModel.model_dump where the password is hashed."""
        data = self.json()
        if isinstance(self.password, str):
            data["password"] = hashpw(self.password.encode(), gensalt())
        return data


class User(UserCommon):
    """User Base Model."""

    id: str
    email: EmailStr
    password: bytes
    root_id: str

    class Collection(UserCollection):
        """UserCollection Integration."""

        @classmethod
        def __document__(cls, doc: dict) -> "User":
            """
            Return parsed User from document.

            This the default User parser after getting a single document.
            You may override this to specify how/which class it will be casted/based.
            """
            return User.model()(
                id=str(doc.pop("_id")),
                email=doc.pop("email"),
                password=doc.pop("password", None) or NULL_BYTES,
                root_id=str(doc.pop("root_id")),
                **doc,
            )

        @classmethod
        def __documents__(cls, docs: list[dict]) -> list["User"]:
            """
            Return list of parsed User from list of document.

            This the default User list parser after getting multiple documents.
            You may override this to specify how/which class it will be casted/based.
            """
            return [
                User.model()(
                    id=str(doc.get("_id")),
                    email=doc.get("email"),
                    password=doc.get("password") or NULL_BYTES,
                    root_id=str(doc.pop("root_id")),
                    **doc,
                )
                for doc in docs
            ]

    @staticmethod
    def model() -> type["User"]:
        """Retrieve the preferred User Model from subclasses else this class."""
        if subs := __class__.__subclasses__():
            return subs[-1]
        return __class__

    @staticmethod
    def register_type() -> type:
        """Generate User Registration Model based on preferred User Model for FastAPI endpoint validation."""
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
        user_model.pop("root_id", None)

        return create_model("UserRegister", __base__=UserCommon, **user_model)
