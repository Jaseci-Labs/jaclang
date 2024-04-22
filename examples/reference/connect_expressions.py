from __future__ import annotations
from jaclang.plugin.feature import JacFeature as jac
from dataclasses import dataclass as jac_dataclass__


@jac.make_node(on_entry=[], on_exit=[])
@jac_dataclass__(eq=False)
class node_a:
    value: int


@jac.make_node(on_entry=[], on_exit=[])
@jac_dataclass__(eq=False)
class node_b:
    val: int


@jac.make_walker(on_entry=[jac.DSFunc("connect", jac.RootType)], on_exit=[])
class Connector:

    def connect(self, jac_here_: jac.RootType) -> None:
        jac.connect(
            left=list_1,
            right=list_2,
            edge_spec=jac.build_edge(
                is_undirected=False, conn_type=None, conn_assign=None
            ),
        )
        print(
            jac.edge_ref(
                list_1,
                target_obj=list_2,
                dir=jac.EdgeDir.OUT,
                filter_func=None,
                edges_only=False,
            )
        )


@jac.make_walker(on_entry=[jac.DSFunc("disconnect", jac.RootType)], on_exit=[])
class Disconnector:

    def disconnect(self, jac_here_: jac.RootType) -> None:
        jac.disconnect(list_1, list_2, "OUT", None)
        print(
            jac.edge_ref(
                list_1,
                target_obj=list_2,
                dir=jac.EdgeDir.OUT,
                filter_func=None,
                edges_only=False,
            )
        )


list_1 = [node_a(value=5) for i in range(0, 5)]
list_2 = [node_b(val=10) for i in range(0, 5)]
jac.spawn_call(jac.get_root(), Connector())
jac.spawn_call(jac.get_root(), Disconnector())
