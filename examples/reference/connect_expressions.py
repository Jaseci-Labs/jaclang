from __future__ import annotations
from jaclang.plugin.feature import JacFeature as _Jac
from jaclang.plugin.builtin import *
from dataclasses import dataclass as __jac_dataclass__


@_Jac.make_node(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class node_a:
    value: int


@_Jac.make_node(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class node_b:
    val: int


list_1 = [node_a(value=5) for i in range(0, 5)]
list_2 = [node_b(val=10) for i in range(0, 5)]
_Jac.connect(
    left=list_1,
    right=list_2,
    edge_spec=_Jac.build_edge(is_undirected=False, conn_type=None, conn_assign=None),
)
print(
    _Jac.edge_ref(
        list_1,
        target_obj=list_2,
        dir=_Jac.EdgeDir.OUT,
        filter_func=None,
        edges_only=False,
    )
)
_Jac.disconnect(list_1, list_2, "OUT", None)
print(
    _Jac.edge_ref(
        list_1,
        target_obj=list_2,
        dir=_Jac.EdgeDir.OUT,
        filter_func=None,
        edges_only=False,
    )
)
