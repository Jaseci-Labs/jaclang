import:py os;
import:py from math, sqrt as square_root;
import:py datetime as dt;
import:jac from base_module_structure, add, subtract;
import:jac from ..micro.func, factorial;

with entry {
    for i in range(int(square_root(dt.datetime.now().year))) {
        print(os.getcwd(), add(i, subtract(i, 1)));
    }
    print(factorial(3));
}
