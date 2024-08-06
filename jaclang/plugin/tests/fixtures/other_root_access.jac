node A {
    has val: int;
}

walker check_node {
    can enter with `root entry {
        visit [-->];
    }

    can enter2 with A entry {
        print(here);
    }
}

walker create_node {
    has val: int;

    can enter with `root entry {
        a = A(val=self.val);
        here ++> a;
        print(a.__jac__.ref_id);
    }
}

walker create_other_root {
    can enter with `root entry {
        other_root = `root();
        other_root.__jac__.sync();
        print(other_root.__jac__.ref_id);
    }
}