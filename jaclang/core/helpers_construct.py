"""Helper for construct."""
from typing import TYPE_CHECKING

from jaclang.compiler.constant import EdgeDir


if TYPE_CHECKING:
    from jaclang.core.construct import NodeArchitype


def dfs(
    current_node: "NodeArchitype",
    visited_nodes: set,
    nodes_list: list,
    connections: set,
) -> None:
    """Traverse through the Nodes."""
    if current_node not in visited_nodes:
        visited_nodes.add(current_node)
        out_edges = current_node.edges.get(EdgeDir.OUT, [])
        in_edges = current_node.edges.get(EdgeDir.IN, [])

        for edge_ in out_edges:
            target__ = edge_._jac_.target
            if target__ not in nodes_list:
                nodes_list.append(target__)
            estabilish_connection(current_node, target__._jac_, connections)
            dfs(target__._jac_, visited_nodes, nodes_list, connections)

        for edge_ in in_edges:
            source__ = edge_._jac_.source
            if source__ not in nodes_list:
                nodes_list.append(source__)
            estabilish_connection(source__._jac_, current_node, connections)
            dfs(source__._jac_, visited_nodes, nodes_list, connections)


def estabilish_connection(
    source_: "NodeArchitype", target_: "NodeArchitype", connections: set
) -> None:
    """Estabilish connection between nodes of a edge."""
    connections.add((source_.obj, target_.obj))
