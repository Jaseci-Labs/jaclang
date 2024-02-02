"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, FastAPI, specs, start;

walker post_no_body {}
walker post_with_body {
    has a: str;
}

@specs(methods=["get"])
walker get_no_body {}

@specs(methods=["get"], as_query=["a"])
walker get_with_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
}

@specs(methods=["get"], as_query="*")
walker get_all_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
    has b: str;
}

@specs(methods=["post", "get"], as_query=["a", "b"])
walker combination {
    has a: str;
    has b: str;
    has c: str;
}

@specs(path = "/{a}", methods=["post"])
walker post_path_var {
    has a: str;
}

@specs(path = "/{a}", methods=["post", "get", "put", "patch", "delete", "head", "trace", "options"], as_query=["b"])
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