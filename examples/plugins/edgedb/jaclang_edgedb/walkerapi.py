from contextvars import ContextVar
import json
import os
from pydoc import locate
import re
import typing
import edgedb
from fastapi import APIRouter, Depends, FastAPI, Request, Response
from .context import JacContext
from pydantic import create_model
from jaclang.compiler.constant import EdgeDir
from jaclang.core.construct import (
    Architype,
    EdgeArchitype,
)
from jaclang.core.construct import Root
from jaclang.plugin.default import hookimpl
from jaclang.plugin.spec import WalkerArchitype, DSFunc, NodeArchitype
from jaclang.cli.cli import cmd_registry

from dataclasses import Field, dataclass
from functools import wraps
from typing import (
    Any,
    List,
    NamedTuple,
    Dict,
    Optional,
    Type,
    Callable,
    TypeVar,
    Union,
    get_origin,
    get_args,
)
from jaclang.plugin.feature import JacFeature as Jac

client = edgedb.create_client()
async_client = edgedb.create_async_client()

JCONTEXT = ContextVar("JCONTEXT")

T = TypeVar("T")

router = APIRouter(prefix="/walker", tags=["walker"])


class DefaultSpecs:
    """Default API specs."""

    path: str = ""
    methods: list[str] = ["post"]
    as_query: Union[str, list[str]] = []
    auth: bool = True


class TypeInfo(NamedTuple):
    type: str
    is_optional: bool
    is_list: bool


@cmd_registry.register
def edgedb_setup():
    # does edgedb toml file exist in the current directory
    if not os.path.exists("edgedb.toml"):
        # run edgedb project init command
        os.system("edgedb project unlink -D")
        os.system("edgedb project init")
    else:
        os.makedirs("dbschema", exist_ok=True)
        # create migration files
        if not os.path.exists("dbschema/Base.esdl"):
            schema_base = """
                using extension auth;
                using extension graphql;
                module default {
                    abstract type Node {
                        required property properties: json;
                        required property name: str;
                    }
                    abstract type Edge {
                        required property name: str;
                        required property properties: json;
                        link from_node: Node;
                        link to_node: Node;
                    }
                    type RootNode extending Node {}
                    type GenericNode extending Node {}
                    type GenericEdge extending Edge {}
                }
            """

            with open("dbschema/Base.esdl", "w") as f:
                f.write(schema_base)

        os.system("edgedb migrate --dev-mode")


def get_root():
    # get root node from edge db
    root_query = "SELECT RootNode {}"
    result = client.query(root_query)
    if len(result) == 0:
        # create root node
        client.query(
            """INSERT RootNode {
                properties := <json>$properties, 
                name := 'RootNode'
            }""",
            properties=json.dumps({}),
        )
        result = client.query(root_query)
        return result[0]

    return result[0]


def insert_node(cls, **kwargs) -> None:
    # create instance in edge db, insert statement
    query = f"""INSERT GenericNode {{
        name := <str>$name,
        properties := <json>$properties
        }};
    """

    result = client.query(query, name=cls.__name__, properties=json.dumps(kwargs))
    # print(result[0].id)
    cls._edge_data = result[0]
    client.close()


def insert_edge(cls, **kwargs) -> None:
    # create instance in edge db, insert statement
    query = f"""INSERT GenericEdge {{
        name := <str>$name,
        properties := <json>$properties
        }};
    """

    result = client.query(query, name=cls.__name__, properties=json.dumps(kwargs))
    # print(result[0].id)
    cls._edge_data = result[0]
    client.close()


def connect_query(id: str, from_node: str, to_node: str):
    query = f"""
    UPDATE Edge 
        filter .id = <uuid>$id
        set {{
            from_node := (select Node
                            filter .id = <uuid>$from_node),
            to_node := (select Node 
                            filter .id = <uuid>$to_node)
        }};
    """
    print(id)
    client.query(query, id=id, from_node=from_node, to_node=to_node)
    client.close()


def disconnect_query(id: str, from_node: str, to_node: str):
    query = f"""
    UPDATE Edge 
        filter .id = <uuid>$id
        set {{
            from_node := {{}},
            to_node := {{}} 
        }};
    """
    client.query(query, id=id, from_node=from_node, to_node=to_node)
    client.close()


def get_specs(cls: type) -> DefaultSpecs:
    """Get Specs and inherit from DefaultSpecs."""
    specs = getattr(cls, "Specs", DefaultSpecs)
    if not issubclass(specs, DefaultSpecs):
        specs = type(specs.__name__, (specs, DefaultSpecs), {})

    return specs


def build_router(cls: Type[WalkerArchitype]) -> APIRouter:
    """Build a FastAPI router for the walker."""
    # read from specs object which determines which fields are query params, and other api metadata
    specs = get_specs(cls)
    as_query: dict = specs.as_query or []

    query = {"nd": (str, "")}
    body = {}

    # if path:
    #     if not path.startswith("/"):
    #         path = f"/{path}"
    #     as_query += PATH_VARIABLE_REGEX.findall(path)

    path = f"/{cls.__name__}"

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

    async def api(
        request: Request,
        body: body_model = None,  # type: ignore
        query: query_model = Depends(),  # type: ignore
    ) -> Response:
        print("NODE", query.nd)
        # jctx = JacContext(request=request)
        # JCONTEXT.set(jctx)
        wlk = cls()
        print(wlk._jac_)
        # node = wlk._jac_.get_node(query.nd)
        if not query.nd:
            root = Root()
            wlk._jac_.spawn_call(Jac.get_root())
        else:
            # get the node from the db
            # create node architype
            # add edges to node object
            # spawn walker on the node

        return "hello"
        # return jctx.response()

    router.post(f"{path.lower()}")(api)

    return router


class JacFeature:
    """Create a walker API."""

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
            build_router(cls)
            return cls

        return decorator

    @staticmethod
    @hookimpl
    def make_node(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create a node architype."""

        def decorator(cls):
            """Decorate class."""
            cls = dataclass(eq=False)(cls)
            for i in on_entry + on_exit:
                i.resolve(cls)
            arch_cls = NodeArchitype
            if not issubclass(cls, arch_cls):
                cls = type(cls.__name__, (cls, arch_cls), {})

            cls._jac_entry_funcs_ = on_entry
            cls._jac_exit_funcs_ = on_exit
            inner_init = cls.__init__

            @wraps(inner_init)
            def new_init(self, *args: object, **kwargs: object) -> None:
                inner_init(self, *args, **kwargs)
                arch_cls.__init__(self)
                insert_node(cls, **kwargs)

            cls.__init__ = new_init

            return cls

        return decorator

    @staticmethod
    @hookimpl
    def make_edge(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create an edge architype."""

        def decorator(cls):
            """Decorate class."""
            cls = dataclass(eq=False)(cls)
            for i in on_entry + on_exit:
                i.resolve(cls)
            arch_cls = EdgeArchitype
            if not issubclass(cls, arch_cls):
                cls = type(cls.__name__, (cls, arch_cls), {})

            cls._jac_entry_funcs_ = on_entry
            cls._jac_exit_funcs_ = on_exit
            inner_init = cls.__init__

            @wraps(inner_init)
            def new_init(self, *args: object, **kwargs: object) -> None:
                inner_init(self, *args, **kwargs)
                arch_cls.__init__(self)
                insert_edge(cls, **kwargs)

            cls.__init__ = new_init

            return cls

        return decorator

    @staticmethod
    @hookimpl
    def connect(
        left: NodeArchitype | list[NodeArchitype],
        right: NodeArchitype | list[NodeArchitype],
        edge_spec: EdgeArchitype,
    ) -> NodeArchitype | list[NodeArchitype]:
        """Jac's connect operator feature.

        Note: connect needs to call assign compr with tuple in op
        """
        if isinstance(left, list):
            if isinstance(right, list):
                for i in left:
                    for j in right:
                        i._jac_.connect_node(j, edge_spec)
            else:
                for i in left:
                    i._jac_.connect_node(right, edge_spec)
        else:
            if isinstance(right, list):
                for i in right:
                    left._jac_.connect_node(i, edge_spec)
            else:
                left._jac_.connect_node(right, edge_spec)

        # connect nodes in edge db
        if isinstance(left, Root):
            root = get_root()
            left_id = root.id
        else:
            left_id = right._edge_data.id

        if isinstance(right, Root):
            root = get_root()
            right_id = root.id
        else:
            right_id = right._edge_data.id

        connect_query(edge_spec._edge_data.id, left_id, right_id)

        return left

    @staticmethod
    @hookimpl
    def disconnect(op1: Optional[T], op2: T, op: Any) -> T:
        """Jac's connect operator feature."""

        return ret if (ret := op1) is not None else op2

    @staticmethod
    @hookimpl
    def visit_node(
        walker: WalkerArchitype,
        expr: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool:
        """Jac's visit stmt feature."""
        print("EXPR", expr)
        if isinstance(walker, WalkerArchitype):
            return walker._jac_.visit_node(expr)
        else:
            raise TypeError("Invalid walker object")

    @staticmethod
    @hookimpl
    def report(expr: Any) -> Any:  # noqa: ANN401
        """Jac's report stmt feature."""
        jctx: JacContext = JCONTEXT.get()
        jctx.report(expr)
