"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, FastAPI, options, start;

walker post_no_body {}
walker post_with_body {
    has a: str;
}

@options(allowed_methods=["get"])
walker get_no_body {}

@options(allowed_methods=["get"], as_query=["a"])
walker get_with_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
}

@options(allowed_methods=["get"], as_query="*")
walker get_all_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
    has b: str;
}

@options(allowed_methods=["post", "get"], as_query=["a", "b"])
walker combination {
    has a: str;
    has b: str;
    has c: str;
}

@options(path = "/{a}", allowed_methods=["post"])
walker post_path_var {
    has a: str;
}

@options(path = "/{a}", allowed_methods=["post", "get"], as_query=["b"])
walker combination2 {
    has a: str;
    has b: str;
    has c: str;
}

with entry:__main__ {
    start(
        host="0.0.0.0",
        port=8000
    );
}