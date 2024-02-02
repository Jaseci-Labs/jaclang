from jaclang.plugin.default import hookimpl
from jaclang.plugin.spec import ArchBound, WalkerArchitype, DSFunc

from dataclasses import dataclass, Field
from functools import wraps
from typing import Type, Callable, Union
from pydantic import create_model
from pydoc import locate
from re import compile

from fastapi import Depends
from jaclang_fastapi import FastAPI


PATH_VARIABLE_REGEX = compile(r"{([^\}]+)}")


class DefaultSpecs:
    path: str = ""
    methods: list[str] = ["post"]
    as_query: Union[str, list[str]] = []


class JacFeature:
    @staticmethod
    @hookimpl
    def make_walker(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create a walker architype."""

        def decorator(cls: Type[ArchBound]) -> Type[ArchBound]:
            """Decorate class."""
            cls = dataclass(eq=False)(cls)
            for i in on_entry + on_exit:
                i.resolve(cls)
            arch_cls = WalkerArchitype
            if not issubclass(cls, arch_cls):
                cls = type(cls.__name__, (cls, arch_cls), {})
            cls._jac_entry_funcs_ = on_entry
            cls._jac_exit_funcs_ = on_exit
            inner_init = cls.__init__

            @wraps(inner_init)
            def new_init(self: ArchBound, *args: object, **kwargs: object) -> None:
                inner_init(self, *args, **kwargs)
                arch_cls.__init__(self)

            cls.__init__ = new_init

            populate_apis(cls)
            return cls

        return decorator


def get_specs(cls):
    specs = getattr(cls, "Specs", DefaultSpecs)
    if not issubclass(specs, DefaultSpecs):
        specs = type(specs.__name__, (specs, DefaultSpecs), {})

    return specs


def populate_apis(cls):
    specs = get_specs(cls)
    path: str = specs.path or ""
    methods: list = specs.methods or []
    as_query: dict = specs.as_query or []

    query = {}
    body = {}

    if path:
        if not path.startswith("/"):
            path = f"/{path}"
        as_query += PATH_VARIABLE_REGEX.findall(path)

    walker_url = f"/walker/{cls.__name__}{path}"

    fields: dict[str, Field] = cls.__dataclass_fields__
    for key, val in fields.items():
        consts = [locate(val.type)]
        if callable(val.default_factory):
            consts.append(val.default_factory())
        else:
            consts.append(...)
        consts = tuple(consts)

        if as_query == "*" or key in as_query:
            query[key] = consts
        else:
            body[key] = consts

    QueryModel = create_model(f"{cls.__name__.lower()}_query_model", **query)
    BodyModel = create_model(f"{cls.__name__.lower()}_body_model", **body)

    if body and query:

        def api(body: BodyModel, query: QueryModel = Depends()):
            return "ok"

    elif body:

        def api(body: BodyModel):
            return "ok"

    elif query:

        def api(query: QueryModel = Depends()):
            return query

    else:

        def api():
            return "ok"

    for method in methods:
        method = method.lower()

        walker_method = getattr(FastAPI, f"walker_{method}")
        walker_method(walker_url)(api)
