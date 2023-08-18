"""Element memory class for Jac."""
import sys
from typing import Optional
from uuid import UUID
from element import Element


#Element = TypeVar("Element") #Fixed 4 errors


class Memory:
    """Memory class for Jac."""

    def __init__(self) -> None:
        """Initialize memory."""
        self.mem: dict[UUID] = {}
        self.save_obj_list = set()
        self._machine = None

    def get_obj(
        self, caller_id: UUID, item_id: UUID, override: bool = False
    ) -> Optional["Element"]:
        """Get item from memory by id, then try store."""
        ret = self.mem.get(item_id)
        if override or (ret is not None and ret.is_readable(caller_id)):
            return ret

    def has_obj(self, item_id: UUID) -> bool:
        """Check if item is in memory."""
        return item_id in self.mem

    def save_obj(self, caller_id: UUID, item: "Element") -> None:
        """Save item to memory."""
        if item.is_writable(caller_id):
            self.mem[item.id] = item
            if item.persist: #fixed 1 more errors
                self.save_obj_list.add(item)

    def destroy_obj(self, caller_id: UUID, item: "Element") -> None:
        """Destroy item from memory."""
        if item.is_writable(caller_id):
            self.mem.pop(item.id)
            if item.persist: #fixed 1 more errors
                self.save_obj_list.remove(item)

    # Utility functions
    # -----------------
    def get_object_distribution(self) -> dict:
        """Get distribution of objects in memory."""
        dist = {}
        for i in self.mem.keys():
            t = type(self.mem[i])
            if t in dist:
                dist[t] += 1
            else:
                dist[t] = 1
        return dist

    def mem_size(self) -> float:
        """Get size of memory in KB."""
        return sys.getsizeof(self.mem) / 1024
