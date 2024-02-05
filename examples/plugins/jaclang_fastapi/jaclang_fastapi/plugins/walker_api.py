from jaclang.core.construct import Architype, DSFunc, WalkerArchitype
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac

from dataclasses import Field
from typing import Type, TypeVar, Callable, Union
from pydantic import create_model
from pydoc import locate
from re import compile

from fastapi import Depends, APIRouter


T = TypeVar("T")
PATH_VARIABLE_REGEX = compile(r"{([^\}]+)}")

router = APIRouter(prefix="/walker", tags=["walker"])


class DefaultSpecs:
    path: str = ""
    methods: list[str] = ["post"]
    as_query: Union[str, list[str]] = []


class JacPlugin:
    @staticmethod
    @hookimpl
    def make_walker(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create a walker architype."""

        def decorator(cls: Type[Architype]) -> Type[Architype]:
            """Decorate class."""
            cls = Jac.make_architype(
                cls=cls, arch_base=WalkerArchitype, on_entry=on_entry, on_exit=on_exit
            )
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

        async def api(body: BodyModel, query: QueryModel = Depends()):
            return "ok"

    elif body:

        async def api(body: BodyModel):
            return "ok"

    elif query:

        async def api(query: QueryModel = Depends()):
            return query

    else:

        async def api():
            return "ok"

    for method in methods:
        method = method.lower()

        walker_method = getattr(router, method)
        walker_method(walker_url, tags=["walker"])(api)


def specs(
    path: str = "", methods: list[str] = [], as_query: Union[str, list] = []
) -> Callable:
    def wrapper(cls: T) -> T:
        p = path
        m = methods
        aq = as_query

        class Specs:
            path: str = p
            methods: list[str] = m
            as_query: Union[str, list] = aq

        cls.Specs = Specs
        return cls

    return wrapper
