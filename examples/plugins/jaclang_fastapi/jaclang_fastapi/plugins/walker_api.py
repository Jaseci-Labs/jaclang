"""Walker API Plugin."""

from dataclasses import Field, dataclass
from inspect import iscoroutine
from pydoc import locate
from re import compile
from typing import Any, Callable, Type, TypeVar, Union

from fastapi import APIRouter, Depends, Request, Response

from jaclang.core.construct import (
    Architype,
    DSFunc,
    WalkerAnchor as _WalkerAnchor,
    WalkerArchitype as _WalkerArchitype,
    root,
)
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac

from pydantic import create_model

from .common import JCONTEXT, JacContext
from ..securities import authenticator


T = TypeVar("T")
PATH_VARIABLE_REGEX = compile(r"{([^\}]+)}")

router = APIRouter(prefix="/walker", tags=["walker"])


class DefaultSpecs:
    """Default API specs."""

    path: str = ""
    methods: list[str] = ["post"]
    as_query: Union[str, list[str]] = []
    auth: bool = True


@dataclass(eq=False)
class WalkerAnchor(_WalkerAnchor):
    """Overriden WalkerAnchor."""

    async def await_if_coroutine(self, ret: Any) -> None:  # noqa: ANN401
        """Await return if it's a coroutine."""
        if iscoroutine(ret):
            ret = await ret

    async def spawn_call(self, nd: Architype) -> None:
        """Invoke data spatial call."""
        self.path = []
        self.next = [nd]
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
    """Plugin Methods."""

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

    @staticmethod
    @hookimpl
    def get_root() -> Architype:
        """Jac's assign comprehension feature."""
        jctx: JacContext = JCONTEXT.get()
        current_root = root
        if jctx:
            current_root = jctx.root
        return current_root

    @staticmethod
    @hookimpl
    def report(expr: Any) -> Any:  # noqa: ANN401
        """Jac's report stmt feature."""
        jctx: JacContext = JCONTEXT.get()
        jctx.report(expr)


def get_specs(cls: type) -> DefaultSpecs:
    """Get Specs and inherit from DefaultSpecs."""
    specs = getattr(cls, "Specs", DefaultSpecs)
    if not issubclass(specs, DefaultSpecs):
        specs = type(specs.__name__, (specs, DefaultSpecs), {})

    return specs


def populate_apis(cls: type) -> None:
    """Generate FastAPI endpoint based on WalkerArchitype class."""
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

    query_model = create_model(f"{cls.__name__.lower()}_query_model", **query)
    body_model = create_model(f"{cls.__name__.lower()}_body_model", **body)

    if body and query:

        async def api(
            request: Request, body: body_model, query: query_model = Depends()  # type: ignore # noqa: B008
        ) -> Response:
            jctx = JacContext(request=request)
            JCONTEXT.set(jctx)
            wlk = cls(**body.model_dump(), **query.model_dump())
            await wlk._jac_.spawn_call(jctx.root)
            return jctx.response()

    elif body:

        async def api(request: Request, body: body_model) -> Response:  # type: ignore
            jctx = JacContext(request=request)
            JCONTEXT.set(jctx)
            wlk = cls(**body.model_dump())
            await wlk._jac_.spawn_call(jctx.root)
            return jctx.response()

    elif query:

        async def api(request: Request, query: query_model = Depends()) -> Response:  # type: ignore # noqa: B008
            jctx = JacContext(request=request)
            JCONTEXT.set(jctx)
            wlk = cls(**query.model_dump())
            await wlk._jac_.spawn_call(jctx.root)
            return jctx.response()

    else:

        async def api(request: Request) -> Response:
            jctx = JacContext(request=request)
            JCONTEXT.set(jctx)
            wlk = cls()
            await wlk._jac_.spawn_call(jctx.root)
            return jctx.response()

    for method in methods:
        method = method.lower()

        walker_method = getattr(router, method)

        settings = {}
        if auth:
            settings["dependencies"] = authenticator

        walker_method(walker_url, tags=["walker"], **settings)(api)


def specs(
    path: str = "",
    methods: list[str] = [],  # noqa: B006
    as_query: Union[str, list] = [],  # noqa: B006
    auth: bool = True,
) -> Callable:
    """Walker Decorator."""

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
