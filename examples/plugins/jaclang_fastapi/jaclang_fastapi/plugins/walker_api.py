"""Walker API Plugin."""

from dataclasses import Field, _MISSING_TYPE, dataclass
from inspect import iscoroutine
from pydoc import locate
from re import compile
from typing import Any, Callable, Optional, Type, TypeVar, Union

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

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
FILE = {
    "File": UploadFile,
    "Files": list[UploadFile],
    "OptFile": Optional[UploadFile],
    "OptFiles": Optional[list[UploadFile]],
}

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


def gen_model_field(cls: type, field: Field, is_file: False) -> tuple[Any]:
    """Generate Specs for Model Field."""
    consts = [cls]
    if not isinstance(field.default, _MISSING_TYPE):
        consts.append(field.default)
    elif callable(field.default_factory):
        consts.append(field.default_factory())
    else:
        consts.append(File(...) if is_file else ...)

    return tuple(consts)


def populate_apis(cls: type) -> None:
    """Generate FastAPI endpoint based on WalkerArchitype class."""
    specs = get_specs(cls)
    path: str = specs.path or ""
    methods: list = specs.methods or []
    as_query: dict = specs.as_query or []
    auth: bool = specs.auth or False

    query = {}
    body = {}
    files = {}

    if path:
        if not path.startswith("/"):
            path = f"/{path}"
        as_query += PATH_VARIABLE_REGEX.findall(path)

    walker_url = f"/{{node}}/{cls.__name__}{path}"

    fields: dict[str, Field] = cls.__dataclass_fields__
    for key, val in fields.items():
        if file_type := FILE.get(val.type):
            files[key] = gen_model_field(file_type, val, True)
        else:
            consts = gen_model_field(locate(val.type), val, True)

            if as_query == "*" or key in as_query:
                query[key] = consts
            else:
                body[key] = consts

    payload = {
        "query": (
            create_model(f"{cls.__name__.lower()}_query_model", **query),
            Depends(),
        ),
        "files": (
            create_model(f"{cls.__name__.lower()}_files_model", **files),
            Depends(),
        ),
    }

    if body:
        payload["body"] = (
            create_model(f"{cls.__name__.lower()}_body_model", **body),
            ...,
        )

    payload_model = create_model(f"{cls.__name__.lower()}_request_model", **payload)

    async def api(
        request: Request,
        node: str,
        payload: payload_model = Depends(),  # type: ignore # noqa: B008
    ) -> Response:
        jctx = JacContext(request=request, entry=node)
        JCONTEXT.set(jctx)

        payload = payload.model_dump()
        wlk = cls(**payload.get("body", {}), **payload["query"], **payload["files"])
        await wlk._jac_.spawn_call(await jctx.get_entry())
        return jctx.response()

    for method in methods:
        method = method.lower()

        walker_method = getattr(router, method)

        settings = {
            "tags": ["walker"],
            "summary": walker_url,
        }
        if auth:
            settings["dependencies"] = authenticator

        walker_method(walker_url, **settings)(api)


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
