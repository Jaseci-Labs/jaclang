"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, FastAPI, start;
import:py from jaclang_fastapi.types, File, Files, OptFile, OptFiles, Defaults;
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

node boy {
    has val1: str, val2: str;
}

node girl {
    has val: str;
}

node someone {
    has val: list = [];
}

walker post_with_body {
    has a: str;

    async can enter1 with `<r> entry {
        report <r>;

        boys = await [-->];
        report boys;
        visit boys;
        return {"sample_return":"1"};
    }

    async can enter2 with boy entry {
        girls = await [-->];
        report girls;
        visit girls;
        return 2;
    }

    async can enter3 with girl entry {
        anyone = await [-->];
        report anyone;
        visit anyone;
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

walker post_with_file {
    has single: File;
    has multiple: Files;
    has singleOptional: OptFile = None;
    has multipleOptional: OptFiles = None;


    async can enter with `<r> entry {
        print(<s>.single);
        print(<s>.multiple);
        print(<s>.singleOptional);
        print(<s>.multipleOptional);
    }
}

walker post_with_body_and_file {
    has val: int;
    has single: File;
    has multiple: Files;
}

walker change_new_girl {
    async can enter1 with `<r> entry {
        boys = await [-->];
        visit boys;

        return "your return";
    }

    async can enter2 with boy entry {
        old = await [-->];
        report old;

        new = girl(val="new");
        <h> ++> new;
        await new.save();

        await old[0].destroy();

        report await [-->];
    }
}

walker test_array {
    async can enter1 with `<r> entry {
         visit await [-->];
    }

    async can enter2 with someone entry {
        <h>.val.append(1);
        <h>.val = <h>.val;
        await <h>.save();
        report <h>;
    }
}

with entry:__main__ {
    start(
        host="0.0.0.0",
        port=8000
    );
}