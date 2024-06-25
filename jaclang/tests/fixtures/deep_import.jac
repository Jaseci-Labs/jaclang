# import:jac deep.deeper;

# with entry {

#     print("dir init val:", deep.deeper.inivar);

# }
import:py sys;

with entry {
    before_mod = list(sys.modules.keys());
}

import:jac deep.one_lev as one_lev;
import:jac from deep.one_lev, olprint;

with entry {
    after_mod = [m for m in sys.modules.keys() if m not in before_mod];
    print(after_mod);
    
    # print(sys.modules["deep.one_lev"]);
}

with entry {
    print(olprint());
}
