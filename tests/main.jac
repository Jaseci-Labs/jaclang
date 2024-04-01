import:jac from utils.file, var_a;
import:jac from utils.file2, orange_apple;
import:jac from utils.file2, Apple;
import:jac from utils.file2, green_apple;

import:py ast;
import:py os;

obj VariableClassFinder:ast.NodeVisitor: { 
    has obj: str,
        found: bool = False;

    can visit_Assign(node:ast.Assign) {
        for target in node.targets {
            if isinstance (target, ast.Name) and target.id == self.obj {
                self.found = True;
                break;
            }
        }
    }
    can visit_AnnAssign(node:ast.AnnAssign) {
        if isinstance(node.target, ast.Name) and node.target.id == self.obj {
            self.found = True;
        }
    }

    can visit_ClassDef(node: ast.ClassDef) {
        if node.name == self.obj {
            self.found = True;
        }
    }

}
obj ImportFinder:ast.NodeVisitor: {
    has imports: set = set();

    can visit_Import(node: ast.Import) {
        for alias in node.names {
            self.imports.add(alias.name);
        }
    }
    can visit_ImportFrom(node: ast.ImportFrom) {
        self.imports.add(node.module);
    }
}

can get_declaration_loc(obj: str, file_path: str = os.path.realpath(__file__)) {
    if file_path.endswith(".jac") {
        file_path = os.path.join(os.path.dirname(file_path), "__jac_gen__", f"{os.path.basename(file_path).replace('.jac', '.py')}");
    }
    with open(file_path, "r") as f {source = f.read();}
    tree = ast.parse(source);
    variable_finder = VariableClassFinder(obj);
    variable_finder.visit(tree);
    if variable_finder.found {return file_path;}

    import_finder = ImportFinder();
    import_finder.visit(tree);
     for _import in import_finder.imports {
        chunks = _import.split('.');
        import_path = os.path.join(os.path.dirname(os.path.dirname(file_path)), *chunks[:-1], "__jac_gen__", f"{chunks[-1]}.py");
        if not os.path.exists(import_path) {continue;}
        did_found = get_declaration_loc(obj, import_path);
        if did_found {return did_found;}
     }       
}

with entry {
    var_b: int = 11;
    red_apple = Apple("red");

    print(get_declaration_loc("var_a"));  # utils/file.py
    print(get_declaration_loc("var_b"));  # main.py
    print(get_declaration_loc("Apple"));  # utils/file.py
    print(get_declaration_loc("red_apple"));  # main.py
    print(get_declaration_loc("green_apple"));  # utils/file.py
    print(get_declaration_loc("orange_apple"));  # utils/file2.py
}