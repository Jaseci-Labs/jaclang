"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, FastAPI, start;
import:py from jaclang_fastapi.models, User as BaseUser;

# if possible to support this native class declaration
::py::
NULL_BYTES = bytes()

class User(BaseUser):
    name: str

    class Collection(BaseUser.Collection):
        @classmethod
        def __document__(cls, doc) -> "User":
            return User.model()(
                id=str(doc.pop("_id")),
                email=doc.pop("email") + "overrided",
                password=doc.pop("password", None) or NULL_BYTES,
                root_id=str(doc.pop("root_id")),
                **doc,
            )
::py::

walker post_no_body {
    async can enter with `<r> entry {
        b = boy(val1="a", val2="b");
        g = girl(val="b");
        b ++> g;
        <r> ++> b;
        await <r>.save();
        return True;
    }
}
walker post_with_body {
    has a: str;

    async can enter with `<r> entry {
        return -->;
    }
}

walker get_no_body {
    obj Specs {
        static has methods: list = ["get"];
    }
}

walker get_with_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;

    obj Specs {
        static has methods: list = ["get"], as_query: list = ["a"];
    }
}

node boy {
    has val1: str, val2: str;
}

node girl {
    has val: str;
}

walker get_all_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
    has b: str;

    obj Specs {
        static has methods: list = ["get"], as_query: list = "*", auth: bool = False;
    }
}

walker combination {
    has a: str;
    has b: str;
    has c: str;

    obj Specs {
        static has methods: list = ["post", "get"], as_query: list = ["a", "b"];
    }
}

walker post_path_var {
    has a: str;

    obj Specs {
        static has path: str = "/{a}", methods: list = ["post", "get"];
    }
}

walker combination2 {
    has a: str;
    has b: str;
    has c: str;

    obj Specs {
        static has path: str = "/{a}", methods: list = ["post", "get", "put", "patch", "delete", "head", "trace", "options"], as_query: list = ["b"];
    }
}

with entry:__main__ {
    start(
        host="0.0.0.0",
        port=8000
    );
}