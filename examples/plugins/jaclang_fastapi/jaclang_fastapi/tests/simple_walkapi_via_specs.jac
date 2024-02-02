"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, FastAPI, start;

walker post_no_body {}
walker post_with_body {
    has a: str;
}

walker get_no_body {
    static has _jac_specs_: dict = {
        "methods": ["get"]
    };
}

walker get_with_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;

    static has _jac_specs_: dict = {
        "methods": ["get"],
        "as_query": ["a"]
    };
}

walker get_all_query {
    # @query - future improvements instead of adding manually on as_query
    has a: str;
    has b: str;

    static has _jac_specs_: dict = {
        "methods": ["get"],
        "as_query": "*"
    };
}

walker combination {
    has a: str;
    has b: str;
    has c: str;

    static has _jac_specs_: dict = {
        "methods": ["post", "get"],
        "as_query": ["a", "b"]
    };
}

walker post_path_var {
    has a: str;

    static has _jac_specs_: dict = {
        "path": "/{a}",
        "methods": ["post", "get"]
    };
}

walker combination2 {
    has a: str;
    has b: str;
    has c: str;

    static has _jac_specs_: dict = {
        "path": "/{a}",
        "methods": ["post", "get"],
        "as_query": ["b"]
    };
}

with entry:__main__ {
    start(
        host="0.0.0.0",
        port=8000
    );
}