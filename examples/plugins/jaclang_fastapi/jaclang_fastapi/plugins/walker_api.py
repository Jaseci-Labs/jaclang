from jaclang.core.construct import (
    Architype,
    DSFunc,
    WalkerArchitype as _WalkerArchitype,
    WalkerAnchor as _WalkerAnchor,
    root,
)
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac

from dataclasses import Field, dataclass
from typing import Type, TypeVar, Callable, Union
from pydantic import create_model
from pydoc import locate
from re import compile

from inspect import iscoroutine
from fastapi import Depends, APIRouter, Request

from jaclang_fastapi.securities import authenticator


T = TypeVar("T")
PATH_VARIABLE_REGEX = compile(r"{([^\}]+)}")

router = APIRouter(prefix="/walker", tags=["walker"])


class DefaultSpecs:
    path: str = ""
    methods: list[str] = ["post"]
    as_query: Union[str, list[str]] = []
    auth: bool = True


@dataclass(eq=False)
class WalkerAnchor(_WalkerAnchor):
    async def await_if_coroutine(self, ret):
        if iscoroutine(ret):
            ret = await ret

        self.returns.append(ret)

    async def spawn_call(self, nd: Architype) -> None:
        """Invoke data spatial call."""
        self.path = []
        self.next = [nd]
        self.returns = []

        while len(self.next):
            nd = self.next.pop(0)
            for i in nd._jac_entry_funcs_:
                if not i.trigger or isinstance(self.obj, i.trigger):
                    if i.func:
                        await self.await_if_coroutine(i.func(nd, self.obj))
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
            for i in self.obj._jac_entry_funcs_:
                if not i.trigger or isinstance(nd, i.trigger):
                    if i.func:
                        await self.await_if_coroutine(i.func(self.obj, nd))
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
            for i in self.obj._jac_exit_funcs_:
                if not i.trigger or isinstance(nd, i.trigger):
                    if i.func:
                        await self.await_if_coroutine(i.func(self.obj, nd))
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
            for i in nd._jac_exit_funcs_:
                if not i.trigger or isinstance(self.obj, i.trigger):
                    if i.func:
                        await self.await_if_coroutine(i.func(nd, self.obj))
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
        self.ignores = []


class WalkerArchitype(_WalkerArchitype):
    """Walker Architype Protocol."""

    def __init__(self) -> None:
        """Create walker architype."""
        self._jac_: WalkerAnchor = WalkerAnchor(obj=self)


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

    @staticmethod
    @hookimpl
    async def spawn_call(op1: Architype, op2: Architype) -> bool:
        """Jac's spawn operator feature."""
        if isinstance(op1, WalkerArchitype):
            await op1._jac_.spawn_call(op2)
        elif isinstance(op2, WalkerArchitype):
            await op2._jac_.spawn_call(op1)
        else:
            raise TypeError("Invalid walker object")
        return True


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
    auth: bool = specs.auth or False

    query = {}
    body = {}

    if path:
        if not path.startswith("/"):
            path = f"/{path}"
        as_query += PATH_VARIABLE_REGEX.findall(path)

    walker_url = f"/{cls.__name__}{path}"

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

        async def api(request: Request, body: BodyModel, query: QueryModel = Depends()):
            wlk = cls(**body.model_dump(), **query.model_dump())
            await wlk._jac_.spawn_call(request.user_root)
            return wlk._jac_.returns

    elif body:

        async def api(request: Request, body: BodyModel):
            wlk = cls(**body.model_dump())
            await wlk._jac_.spawn_call(request.user_root)
            return wlk._jac_.returns

    elif query:

        async def api(request: Request, query: QueryModel = Depends()):
            wlk = cls(**query.model_dump())
            await wlk._jac_.spawn_call(request.user_roott)
            return wlk._jac_.returns

    else:

        async def api(request: Request):
            wlk = cls()
            await wlk._jac_.spawn_call(request.user_root)
            return wlk._jac_.returns

    for method in methods:
        method = method.lower()

        walker_method = getattr(router, method)

        settings = {}
        if auth:
            settings["dependencies"] = authenticator

        walker_method(walker_url, tags=["walker"], **settings)(api)


def specs(
    path: str = "",
    methods: list[str] = [],
    as_query: Union[str, list] = [],
    auth: bool = True,
) -> Callable:
    def wrapper(cls: T) -> T:
        p = path
        m = methods
        aq = as_query
        a = auth

        class Specs:
            path: str = p
            methods: list[str] = m
            as_query: Union[str, list] = aq
            auth: bool = a

        cls.Specs = Specs
        return cls

    return wrapper
