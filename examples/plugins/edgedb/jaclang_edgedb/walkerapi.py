import inspect
import json
import os
import re
import typing
from typing_extensions import TypedDict, Unpack
import edgedb
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Header,
    Query,
    Request,
    Response,
    Security,
)
from fastapi.security import APIKeyHeader
from jaclang_edgedb.queries import delete_node, get_node, get_node_edges, update_node
from .context import JCONTEXT, JacContext
from pydantic import create_model
from jaclang.compiler.constant import EdgeDir
from jaclang.core.construct import Architype, EdgeArchitype, NodeArchitype
from jaclang.core.construct import Root
from jaclang.plugin.default import hookimpl
from jaclang.plugin.spec import WalkerArchitype, DSFunc
from jaclang.cli.cli import cmd_registry

from dataclasses import dataclass, make_dataclass
from functools import wraps
from typing import (
    Annotated,
    Any,
    NamedTuple,
    Optional,
    Type,
    Callable,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
from jaclang.plugin.feature import JacFeature as Jac

client = edgedb.create_client()
async_client = edgedb.create_async_client()


def to_snake_case(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("__([A-Z])", r"_\1", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


T = TypeVar("T")

router = APIRouter(prefix="/walker", tags=[])


class DefaultSpecs:
    """Default API specs."""

    tags: str = [""]
    exclude: bool = False
    method: str = "post"


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
    client.close()
    return result[0]


def insert_edge(cls, **kwargs) -> None:
    # create instance in edge db, insert statement
    query = f"""INSERT GenericEdge {{
        name := <str>$name,
        properties := <json>$properties
        }};
    """

    result = client.query(query, name=cls.__name__, properties=json.dumps(kwargs))
    client.close()

    return result[0]


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


def build_dataclass_model(name: str, fields: dict[str, type], origin_cls: type) -> Any:
    """Build a dataclass model from a dict."""
    model_fields = []

    for key, val in fields.items():
        if key == "nd":
            model_fields.append((key, val, None))
        else:
            if callable(origin_cls.__dataclass_fields__[key].default_factory):
                model_fields.append(
                    (key, val, origin_cls.__dataclass_fields__[key].default_factory())
                )
            else:
                model_fields.append((key, val))

    Model = make_dataclass(name, model_fields)

    return Model


def build_router(cls: Type[WalkerArchitype]) -> APIRouter:
    """Build a FastAPI router for the walker."""
    # read from specs object which determines which fields are query params, and other api metadata
    specs = get_specs(cls)

    body = {}

    # if path:
    #     if not path.startswith("/"):
    #         path = f"/{path}"
    #     as_query += PATH_VARIABLE_REGEX.findall(path)

    path = f"/{to_snake_case(cls.__name__)}"

    cls_fields = cls
    cls_fields = typing.get_type_hints(cls, include_extras=True)
    body = {}

    form_fields = {}
    query_fields = {}
    header_fields = {}
    security_fields = {}

    for key, val in cls_fields.items():
        if key.startswith("_"):
            continue

        if key in form_fields.keys():
            continue

        # check for form and query fields
        if get_args(val) and get_origin(val) is Annotated:
            arg_classes = [c.__class__ for c in get_args(val)]
            is_form_field = (
                Form().__class__ in arg_classes or File().__class__ in arg_classes
            )

            is_query_field = Query().__class__ in arg_classes
            is_header_field = Header().__class__ in arg_classes

            is_security_field = Security().__class__ in arg_classes

            if is_form_field:
                form_fields[key] = val
                continue
            elif is_query_field:
                query_fields[key] = val
                continue
            elif is_header_field:
                header_fields[key] = val
                continue
            elif is_security_field:
                security_fields[key] = val
                continue

        default_val = ...

        if callable(cls.__dataclass_fields__[key].default_factory):
            default_val = cls.__dataclass_fields__[key].default_factory()

        body[key] = (val, default_val)

    body_model = create_model(f"{cls.__name__.lower()}_body_model", **body)

    async def api_fn(
        request: Request,
        body: body_model = None,  # type: ignore
        query: dict = None,
        headers: dict = None,
        security: dict = None,
        **kwargs: Any,
    ) -> Response:
        # make the request object available to the walker
        cls.get_request = lambda self: request

        jctx = JacContext(request=request)
        JCONTEXT.set(jctx)
        input = {}

        if body and hasattr(body, "model_dump"):
            input.update(body.model_dump())
        elif body and isinstance(body, dict):
            input.update(body)

        if query:
            input.update(query)
            # we need to remove the nd field from the input, as it's not a field of the walker
            # but it is always present in the query
            del input["nd"]

        if headers:
            input.update(headers)

        if security:
            input.update(security)

        wlk = cls(**input)

        if not query["nd"]:
            db_root = get_root()
            root_node = Jac.get_root()
            root_node._edge_data = db_root
            wlk._jac_.spawn_call(root_node)
        else:
            db_node = await get_node(async_client, query["nd"])

            if not db_node:
                raise HTTPException(status_code=404, detail="Node not found")

            node_type = JacFeature._node_types[db_node.name]

            if not node_type:
                raise HTTPException(detail="Node type not found", status_code=404)

            node: NodeArchitype = node_type(
                **json.loads(db_node.properties), _edge_data=db_node
            )

            wlk._jac_.spawn_call(node)
            pass
        return jctx.response()

    # setup query fields
    query_fields.update({"nd": str})

    QueryModel = build_dataclass_model(f"{cls.__name__}_query_model", query_fields, cls)
    HeaderModel = build_dataclass_model(
        f"{cls.__name__}_header_model", header_fields, cls
    )
    SecurityModel = build_dataclass_model(
        f"{cls.__name__}_security_model", security_fields, cls
    )

    if specs.method.lower() == "get":

        async def api(
            request: Request,
            query: QueryModel = Depends(),  # type: ignore
            headers: HeaderModel = Depends(),  # type: ignore
            security: SecurityModel = Depends(),  # type: ignore
        ) -> Response:
            return await api_fn(
                request,
                query=query.__dict__,
                headers=headers.__dict__,
                security=security.__dict__,
            )

    else:

        async def api(
            request: Request,
            body: body_model = None,  # type: ignore
            query: QueryModel = Depends(),  # type: ignore
            headers: HeaderModel = Depends(),  # type: ignore
            security: SecurityModel = Depends(),  # type: ignore
        ) -> Response:
            return await api_fn(
                request,
                body,
                query.__dict__,
                headers=headers.__dict__,
                security=security.__dict__,
            )

    if form_fields:
        FormModel = build_dataclass_model(
            f"{cls.__name__.lower()}_body_model", form_fields, cls
        )

        # when using form fields, the api function signature changes
        # we no longer accept json body, but instead accept form fields
        async def api(
            request: Request,
            query: QueryModel = Depends(),  # type: ignore
            form: FormModel = Depends(),  # type: ignore
            headers: HeaderModel = Depends(),  # type: ignore
            security: SecurityModel = Depends(),  # type: ignore
        ) -> Response:
            return await api_fn(
                request,
                form.__dict__,
                query.__dict__,
                headers=headers.__dict__,
                security=security.__dict__,
            )

    if not specs.exclude:
        getattr(router, specs.method.lower())(f"{path.lower()}", tags=specs.tags)(api)

    return router


class JacFeature:
    """Create a walker API."""

    _node_types = {}
    _edge_types = {}

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
            inner_setattr = cls.__setattr__

            @wraps(inner_init)
            def new_init(
                self, _edge_data=None, *args: object, **kwargs: object
            ) -> None:
                inner_init(self, *args, **kwargs)
                arch_cls.__init__(self)

                # here we are accessing the node from the db, via walker api, so no need
                # to insert node
                if _edge_data:
                    self._edge_data = _edge_data

                if not hasattr(self, "_edge_data"):
                    self._edge_data = insert_node(cls, **kwargs)

            @wraps(inner_setattr)
            def new_setattr(self, __name: str, __value: Any) -> None:
                """Intercept changes to node properties and update the db."""

                if __name != "_edge_data" and __name != "_jac_":
                    # only update if the attribute exists already
                    if hasattr(self, __name) and hasattr(self, "_edge_data"):
                        properties = json.loads(self._edge_data.properties)
                        properties[__name] = __value
                        properties = json.dumps(properties)
                        update_node(client, self._edge_data.id, properties)

                return inner_setattr(self, __name, __value)

            cls.__init__ = new_init
            cls.__setattr__ = new_setattr
            cls.destroy = lambda self: delete_node(
                client=client, uuid=self._edge_data.id
            )

            # track node types
            JacFeature._node_types[cls.__name__] = cls

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
            def new_init(
                self, _edge_data=None, *args: object, **kwargs: object
            ) -> None:
                inner_init(self, *args, **kwargs)
                arch_cls.__init__(self)

                # here we are accessing the node from the db, via walker api, so no need
                # to insert node
                if _edge_data:
                    self._edge_data = _edge_data

                if not hasattr(self, "_edge_data"):
                    self._edge_data = insert_edge(cls, **kwargs)

            cls.__init__ = new_init

            # track edge types
            JacFeature._edge_types[cls.__name__] = cls

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
            left_id = left._edge_data.id

        if isinstance(right, Root):
            root = get_root()
            right_id = root.id
        else:
            right_id = right._edge_data.id

        connect_query(edge_spec._edge_data.id, left_id, right_id)

        return left

    # @staticmethod
    # @hookimpl
    # def disconnect(op1: Optional[T], op2: T, op: Any) -> T:
    #     """Jac's connect operator feature."""

    #     return ret if (ret := op1) is not None else op2

    @staticmethod
    @hookimpl
    def visit_node(
        walker: WalkerArchitype,
        expr: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool:
        """Jac's visit stmt feature."""
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

    # @staticmethod
    # @hookimpl
    # def edge_ref(
    #     node_obj: NodeArchitype,
    #     dir: EdgeDir,
    #     filter_type: Optional[type],
    #     filter_func: Optional[Callable],
    # ) -> list[NodeArchitype]:
    #     """Jac's apply_dir stmt feature."""
    #     if isinstance(node_obj, NodeArchitype):
    #         node_obj._jac_.edges[EdgeDir.IN] = []
    #         node_obj._jac_.edges[EdgeDir.OUT] = []

    #         db_edges = get_node_edges(client, node_obj._edge_data.id)
    #         for edge in db_edges:
    #             # create the edge architype
    #             # source node
    #             if edge.from_node.id == node_obj._edge_data.id:
    #                 from_node_obj = node_obj
    #             else:
    #                 # root node is named RootNode in the db, this node type isn't defined anywhere in the jac code
    #                 if edge.from_node.name == "RootNode":
    #                     from_node_obj = Jac.get_root()
    #                     from_node_obj._edge_data = edge.from_node
    #                 else:
    #                     from_node_cls = JacFeature._node_types[edge.from_node.name]
    #                     from_node_obj: NodeArchitype = from_node_cls(
    #                         **json.loads(edge.from_node.properties),
    #                         _edge_data=edge.from_node,
    #                     )

    #             # target node
    #             if edge.to_node.id == node_obj._edge_data.id:
    #                 to_node_obj = node_obj
    #             else:
    #                 if edge.to_node.name == "RootNode":
    #                     to_node_cls = Jac.get_root()
    #                     to_node_cls._edge_data = edge.to_node
    #                 else:
    #                     to_node_cls = JacFeature._node_types[edge.to_node.name]
    #                     to_node_obj: NodeArchitype = to_node_cls(
    #                         **json.loads(edge.to_node.properties),
    #                         _edge_data=edge.to_node,
    #                     )

    #             edge_cls = JacFeature._edge_types[edge.name]
    #             edge_obj: EdgeArchitype = edge_cls(
    #                 **json.loads(edge.properties), _edge_data=edge
    #             )
    #             edge_obj._jac_.apply_dir(dir)
    #             edge_obj._jac_.attach(src=from_node_obj, trg=to_node_obj)

    #         return node_obj._jac_.edges_to_nodes(dir, filter_type, filter_func)
    #     else:
    #         raise TypeError("Invalid node object")
    @staticmethod
    @hookimpl
    def edge_ref(
        node_obj: NodeArchitype | list[NodeArchitype],
        target_obj: Optional[NodeArchitype | list[NodeArchitype]],
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        edges_only: bool,
    ) -> list[NodeArchitype] | list[EdgeArchitype]:
        """Jac's apply_dir stmt feature."""
        if isinstance(node_obj, NodeArchitype):
            db_edges = get_node_edges(client, node_obj._edge_data.id)

            for edge in db_edges:
                # create the edge architype
                # grab source node
                if edge.from_node.id == node_obj._edge_data.id:
                    from_node_obj = node_obj
                else:
                    # root node is named RootNode in the db, this node type isn't defined anywhere in the jac code
                    if edge.from_node.name == "RootNode":
                        from_node_obj = Jac.get_root()
                        from_node_obj._edge_data = edge.from_node
                    else:
                        from_node_cls = JacFeature._node_types[edge.from_node.name]
                        from_node_obj: NodeArchitype = from_node_cls(
                            **json.loads(edge.from_node.properties),
                            _edge_data=edge.from_node,
                        )

                # grab target node
                if edge.to_node.id == node_obj._edge_data.id:
                    to_node_obj = node_obj
                else:
                    if edge.to_node.name == "RootNode":
                        to_node_cls = Jac.get_root()
                        to_node_cls._edge_data = edge.to_node
                    else:
                        to_node_cls = JacFeature._node_types[edge.to_node.name]
                        to_node_obj: NodeArchitype = to_node_cls(
                            **json.loads(edge.to_node.properties),
                            _edge_data=edge.to_node,
                        )

                # build the edge class obj
                edge_cls = JacFeature._edge_types[edge.name]
                edge_obj: EdgeArchitype = edge_cls(
                    **json.loads(edge.properties), _edge_data=edge
                )

                # attach the edge to the source and target nodes
                edge_obj._jac_.attach(src=from_node_obj, trg=to_node_obj)

            node_obj = [node_obj]

        targ_obj_set: Optional[list[NodeArchitype]] = (
            [target_obj]
            if isinstance(target_obj, NodeArchitype)
            else target_obj if target_obj else None
        )

        if edges_only:
            connected_edges: list[EdgeArchitype] = []
            for node in node_obj:
                connected_edges += node._jac_.get_edges(
                    dir, filter_func, target_obj=targ_obj_set
                )
            return list(set(connected_edges))
        else:
            connected_nodes: list[NodeArchitype] = []
            for node in node_obj:
                connected_nodes.extend(
                    node._jac_.edges_to_nodes(dir, filter_func, target_obj=targ_obj_set)
                )
            return list(set(connected_nodes))
