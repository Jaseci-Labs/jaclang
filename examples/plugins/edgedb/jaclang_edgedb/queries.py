import json
from edgedb import AsyncIOClient
from pydantic import BaseModel


class DBNode(BaseModel):
    id: str
    name: str
    properties: str


async def get_node(client: AsyncIOClient, uuid: str) -> DBNode:
    query = """
        SELECT Node {**}
        filter .id = <uuid>$uuid;
    """
    result = await client.query_single(query, uuid=uuid)
    return result
