from jaclang.core.construct import NodeArchitype as NodeArchitype
from typing import Optional

def dotgen(
    node: Optional[NodeArchitype] = None,
    depth: Optional[int] = None,
    traverse: Optional[bool] = None,
    edge_type: Optional[list[str]] = None,
    bfs: Optional[bool] = None,
    edge_limit: Optional[int] = None,
    node_limit: Optional[int] = None,
    dot_file: Optional[str] = None,
) -> str: ...
