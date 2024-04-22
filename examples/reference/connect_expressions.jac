node node_a {
    has value: int;
}
node node_b {
    has val:int;
}

walker Connector{
    can connect with `root entry;
}

walker Disconnector{
    can disconnect with `root entry;
}

:walker:Connector:can:connect {
    #connecting the list of nodes to another list of nodes
    list_1 ++> list_2;
    print([list_1-->list_2]);
    #print(dotgen(list_1[1]));
    }

:walker:Disconnector:can:disconnect {
    #disconnecting the list_1 nodes and list_2 nodes
    list_1 del-->list_2;
    print([list_1-->list_2]);
    #print(dotgen(list_1[1]));
    }

with entry{
    list_1 = [node_a(value=5) for i in range(0,5)];
    list_2 = [node_b(val=10) for i in range(0,5)];

    root spawn Connector();
    root spawn Disconnector();

}

