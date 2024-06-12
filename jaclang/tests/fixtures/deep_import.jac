# import:jac deep.deeper;

# with entry {
#     print("dir init val:", deep.deeper.inivar);
# }

import:jac deep.one_lev as one_lev;
import:jac from deep.one_lev, olprint;

with entry {
    # print(olprint());
    print("olprint type:", type(olprint));
}
