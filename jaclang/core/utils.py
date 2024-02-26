"""Helper for construct."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from jaclang.core.construct import NodeAnchor


def collect_node_connections(
    current_node: NodeAnchor,
    visited_nodes: set,
    connections: set,
) -> None:
    """Nodes and edges representing the graph are collected in visited_nodes and connections."""
    if current_node not in visited_nodes:
        visited_nodes.add(current_node)
        for edge in [*current_node.edges_in, *current_node.edges_out]:
            target = edge._jac_.target
            if target:
                connections.add(
                    (current_node.obj, target._jac_.obj, edge.__class__.__name__)
                )
                collect_node_connections(target._jac_, visited_nodes, connections)
