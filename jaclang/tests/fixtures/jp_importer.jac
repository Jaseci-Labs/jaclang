import:py sys;
import:py from math, sin as s, cos, sqrt as sq;
include:py random;
with entry {before = list(sys.modules.keys());}
import:py from ..test_cli, JacCliTests as Jac;
with entry {print([x for x in sys.modules.keys() if x not in before]);}
with entry {before = list(sys.modules.keys());}

with entry {print("Deep in?", "deep" in list(sys.modules.keys()));}
import:jac from deep.mycode, code as c;
with entry {print([x for x in sys.modules.keys() if x not in before]);}
with entry {print(sys.modules['deep']);}
with entry {print(sys.modules['deep'].__path__);}
import:py from deep.mycode_py, code as py_c;
import:py from deep.othercode_py, foo as py_foo;

import:jac deep.mycode;
import:jac hashcheck as h, assign_compr as a;
include:jac ignore;
import:jac from jacsamp, my_print as m;


with entry{
    print(sq(4), s(30),cos(30));
    print(randint(1, 10));
    print(deep.mycode);
    print(m("--->my_print<---"));
    print(h.a, a.mvar);
    print(c());
    print(py_c());
    }