import:py from jaclang.runtimelib.architype {Anchor}

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

walker update_node {
    has val: int;

    can enter2 with A entry {
        here.val = self.val;
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

walker allow_other_root_access {
    has root_id: str, level: int | str = 0, via_all: bool = False;

    can enter_root with `root entry {
        if self.via_all {
            here.__jac__.unrestrict(self.level);
        } else {
            here.__jac__.allow_root(Anchor.ref(self.root_id), self.level);
        }
    }

    can enter_nested with A entry {
        if self.via_all {
            here.__jac__.unrestrict(self.level);
        } else {
            here.__jac__.allow_root(Anchor.ref(self.root_id), self.level);
        }
    }
}

walker disallow_other_root_access {
    has root_id: str, via_all: bool = False;

    can enter_root with `root entry {
        if self.via_all {
            here.__jac__.restrict();
        } else {
            here.__jac__.disallow_root(Anchor.ref(self.root_id));
        }
    }

    can enter_nested with A entry {
        if self.via_all {
            here.__jac__.restrict();
        } else {
            here.__jac__.disallow_root(Anchor.ref(self.root_id));
        }
    }
}