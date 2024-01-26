"""Example of simple walker walking nodes."""
import:py from jaclang_fastapi, fapi, jget, jpost, jput, jdelete, jhead, joptions, jtrace, start;

@fapi("get", "/")
can home () {}

@jget("/test")
can get () {}

@jpost("/test")
can post () {}

@jput("/test")
can put () {}

@jdelete("/test")
can delete () {}

@jhead("/test")
can head () {}

@joptions("/test")
can options () {}

@jtrace("/test")
can trace () {}

with entry:__main__ {
    start(
        host="0.0.0.0",
        port=8000
    );
}