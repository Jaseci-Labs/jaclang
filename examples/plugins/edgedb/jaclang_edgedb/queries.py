import json
from edgedb import AsyncIOClient, Client
from pydantic import BaseModel


class DBNode(BaseModel):
    id: str
    name: str
    properties: str


class DBEdge(BaseModel):
    id: str
    name: str
    properties: str
    from_node: DBNode
    to_node: DBNode


async def get_node(client: AsyncIOClient, uuid: str) -> DBNode:
    query = """
        SELECT Node {**}
        filter .id = <uuid>$uuid;
    """
    result = await client.query_single(query, uuid=uuid)
    await client.aclose()
    return result


def get_node_edges(client: Client, uuid: str) -> list[DBEdge]:
    query = """
        SELECT Edge {**}
        filter .from_node.id = <uuid>$uuid or .to_node.id = <uuid>$uuid;
    """
    result = client.query(query, uuid=uuid)
    client.close()
    return result


def update_node(client: Client, uuid: str, properties=str) -> DBNode:
    query = """
        UPDATE Node
        filter .id = <uuid>$uuid
        set {properties := <json>$properties};
    """
    result = client.query(query, uuid=uuid, properties=properties)
    client.close()
    return result


def update_edge(client: Client, uuid: str, properties=str) -> DBNode:
    query = """
        UPDATE Node
        filter .id = <uuid>$uuid
        set {properties := <json>$properties};
    """
    result = client.query(query, uuid=uuid, properties=properties)
    client.close()
    return result


def delete_node(client: Client, uuid: str) -> bool:
    delete_edges_query = """
        DELETE Edge
        filter .from_node.id = <uuid>$uuid or .to_node.id = <uuid>$uuid;
    """
    delete_node_query = """
        DELETE Node
        filter .id = <uuid>$uuid;
    """
    for tx in client.transaction():
        with tx:
            tx.query(delete_edges_query, uuid=uuid)
            result = tx.query(delete_node_query, uuid=uuid)
    client.close()
    return result
