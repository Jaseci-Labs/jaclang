"""Definitions of the walker and abilities."""

:walker:travelor:ability:say_hello {
    "Hello" |> print;  # |> is a pipe forward operator
}

# :w: and :a: are aliases for :walker: and :abilitiy:
:w:travelor:a:say_whatever(msg: str) -> None {
    msg |> print;
}