"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, FastAPI, start;
import:py from jaclang_fastapi.models, User as BaseUser;

# if possible to support this native class declaration
::py::
class User(BaseUser):
    name: str
::py::

walker post_no_body {}
walker post_with_body {
    has a: str;
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

walker get_all_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
    has b: str;

    obj Specs {
        static has methods: list = ["get"], as_query: list = "*", auth: bool = False;
    }

    can enter with `<r> entry {
        return 1;
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