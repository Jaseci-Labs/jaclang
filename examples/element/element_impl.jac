"""Implementation for Jac's Element Abstractions"""
import:py sys;


:enum:AccessMode {
    READ_ONLY,
    READ_WRITE,
    PRIVATE
}

:object:Memory:ability:get_obj
(caller_id: UUID, item_id: UUID, override: bool = False) -> Element? {
    ret = item_id |> <here>.index.get;
    if override or (ret is not None and caller_id |> ret.__is_readable) {
        return ret;
    }
}

:object:Memory:ability:has_obj
(item_id: UUID) -> bool {
    return item_id in <here>.index;
}

:object:Memory:ability:save_obj
(caller_id: UUID, item: Element) {
    if caller_id |> item.is_writable {
        <here>.index[item.id] = item;
        if item._persist {
            item |> <here>.save_obj_list.add;
        }
    }
    <here>.mem[item.id] = item;
    if item._persist {
        item |> <here>.save_obj_list.add;
    }
}

:object:Memory:ability:del_obj
(caller_id: UUID, item: Element) {
    if caller_id |> item.is_writable {
        <here>.index.pop(item.id);
        if item._persist {
            item |> <here>.save_obj_list.remove;
        }
    }
}

:object:Memory:ability:get_object_distribution -> dict {
    dist = {};
    for i in |> <here>.index.keys {
        t = <here>.index[i] |> type;
        if t in dist {
            dist[t] += 1;
        }
        else {
            dist[t] = 1;
        }
    }
    return dist;
}

:object:Memory:ability:get_mem_size -> float {
    return (<here>.index |> sys.getsizeof) / 1024.0;
}

:object:Element:ability:init
(owner_id: UUID, memory: Memory, jid: UUID, persist: bool = False) {
    <here>.jinfo.owner_id = owner_id;
    <here>.jinfo.memory = memory;
    <here>.jinfo.id = jid;
    <here>.jinfo._persist = persist;
}

:object:Element:ability:make_public_ro {
    <here>.jinfo.access_mode = AccessMode.READ_ONLY;
}

:object:Element:ability:make_public_rw {
    <here>.jinfo.access_mode = AccessMode.READ_WRITE;
}

:object:Element:ability:make_private {
    <here>.jinfo.access_mode = AccessMode.PRIVATE;
}

:object:Element:ability:is_public_ro -> bool {
    return <here>.jinfo.access_mode == AccessMode.READ_ONLY;
}

:object:Element:ability:is_public_rw -> bool {
    return <here>.jinfo.access_mode == AccessMode.READ_WRITE;
}

:object:Element:ability:is_private -> bool {
    return <here>.jinfo.access_mode == AccessMode.PRIVATE;
}

:object:Element:ability:is_readable
(caller_id: UUID) -> bool{
    return (
            caller_id == <here>.owner_id
            or |> <here>.is_public_read
            or caller_id in <here>.ro_access
            or caller_id in <here>.rw_access
        );
}

:object:Element:ability:is_writable
(caller_id: UUID) -> bool {
    return (
            caller_id == <here>.owner_id
            or |> <here>.is_public_write
            or caller_id in <here>.rw_access
        );
}

:object:Element:ability:give_access
(caller_id: UUID, read_write: bool = False) {
    if read_write {
        caller_id |> <here>.rw_access.add;
    }
    else {
        caller_id |> <here>.ro_access.add;
        caller_id |> add.>ro_access.><here>;
    }
}

:object:Element:ability:revoke_access
(caller_id: UUID) {
    caller_id |> <here>.ro_access.discard;
    caller_id |> <here>.rw_access.discard;
}

with entry {
    "Loaded correctly" |> print;
}