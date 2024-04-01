from utils.file import var_a
from utils.file2 import orange_apple

# from utils.file import Apple
from utils.file2 import Apple
# from utils.file import green_apple
from utils.file2 import green_apple

import ast
import os
import time


def get_declaration_loc(obj: str, file_path=os.path.realpath(__file__)):
    with open(file_path, 'r') as f:
        source = f.read()
        tree = ast.parse(source, file_path)
        variable_finder = VariableClassFinder(obj)
        variable_finder.visit(tree)
        if variable_finder.found:
            return file_path
        import_finder = ImportFinder()
        import_finder.visit(tree)
        for _import in import_finder.imports:
            chunks = _import.split('.')
            import_path = os.path.join(os.path.dirname(file_path), *chunks[:-1], f"{chunks[-1]}.py")
            did_found = get_declaration_loc(obj, import_path)
            if did_found:
                return import_path


class ImportFinder(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.imports.add(node.module)


class VariableClassFinder(ast.NodeVisitor):
    def __init__(self, obj):
        self.obj = obj
        self.found = False

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == self.obj:
                self.found = True

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id == self.obj:
            self.found = True
    
    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name == self.obj:
            self.found = True

var_b = 11
red_apple = Apple("red")


start_t = time.time()
print(get_declaration_loc("var_a"))  # utils/file.py
print(get_declaration_loc("var_b"))  # main.py
print(get_declaration_loc("Apple"))  # utils/file.py
print(get_declaration_loc("red_apple"))  # main.py
print(get_declaration_loc("green_apple"))  # utils/file.py
print(get_declaration_loc("orange_apple"))  # utils/file2.py
print(time.time() - start_t)


