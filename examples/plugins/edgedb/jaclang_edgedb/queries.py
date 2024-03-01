from asyncio import sleep
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


async def get_node_edges(client: AsyncIOClient, uuid: str) -> list[DBEdge]:
    query = """
        SELECT Edge {**}
        filter .from_node.id = <uuid>$uuid or .to_node.id = <uuid>$uuid;
    """
    await sleep(5)
    print("STARTING")
    result = await client.query(query, uuid=uuid)
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


async def insert_node(client: AsyncIOClient, cls_name: str, **kwargs) -> None:
    # create instance in edge db, insert statement
    query = f"""INSERT GenericNode {{
        name := <str>$name,
        properties := <json>$properties
        }};
    """

    result = await client.query(query, name=cls_name, properties=json.dumps(kwargs))
    # client.close()
    return result[0]


async def insert_edge(client: AsyncIOClient, cls_name: str, **kwargs) -> None:
    # create instance in edge db, insert statement
    query = f"""INSERT GenericEdge {{
        name := <str>$name,
        properties := <json>$properties
        }};
    """

    result = await client.query(query, name=cls_name, properties=json.dumps(kwargs))
    # client.close()

    return result[0]


async def connect_query(client: AsyncIOClient, id: str, from_node: str, to_node: str):
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
    await client.query(query, id=id, from_node=from_node, to_node=to_node)
    # client.close()


async def disconnect_query(
    client: AsyncIOClient, id: str, from_node: str, to_node: str
):
    query = f"""
    UPDATE Edge 
        filter .id = <uuid>$id
        set {{
            from_node := {{}},
            to_node := {{}} 
        }};
    """
    await client.query(query, id=id, from_node=from_node, to_node=to_node)
    # client.close()
