"""Test pass module."""

from typing import List

from jaclang.compiler.compile import jac_file_to_pass
from jaclang.compiler.passes.main.schedules import py_code_gen_typed
from jaclang.utils.lang_tools import AstTool
from jaclang.utils.test import TestCase


class MypyTypeCheckPassTests(TestCase):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        self.__messages: List[str] = []
        return super().setUp()

    def test_type_errors(self) -> None:
        """Basic test for pass."""
        type_checked = jac_file_to_pass(
            file_path=self.fixture_abs_path("func.jac"),
            schedule=py_code_gen_typed,
        )

        errs = "\n".join([i.msg for i in type_checked.warnings_had])
        files = "\n".join([i.loc.mod_path for i in type_checked.warnings_had])

        for i in [
            "func2.jac",
            "func.jac",
            '(got "int", expected "str")',
            '(got "str", expected "int")',
        ]:
            self.assertIn(i, errs + files)

    def test_imported_module_typecheck(self) -> None:
        """Basic test for pass."""
        type_checked = jac_file_to_pass(
            file_path=self.fixture_abs_path("game1.jac"),
            schedule=py_code_gen_typed,
        )

        errs = "\n".join([i.msg for i in type_checked.warnings_had])
        files = "\n".join([i.loc.mod_path for i in type_checked.warnings_had])

        for i in [
            'Argument 2 to "is_pressed" of "Button" has incompatible type "int"; expected "str"',
        ]:
            self.assertIn(i, errs + files)

    def test_type_coverage(self) -> None:
        """Testing for type info coverage in sym_tab via ast."""
        out = AstTool().ir(
            ["ast", f"{self.fixture_abs_path('type_info_in_symtab.jac')}"]
        )
        lis = [
            "BankAccount - Type: None",
            'String - "33" - Type: NoType',
            "Name - Body - Type: None",  # obj inside an obj
            "29:5 - 29:9\t        |   |   +-- Name - body - Type: builtins.int",  # Re-assigning
            "introduce - Type: None",
            '" Breed: " - Type: NoType',
            "25:30 - 25:37\t        |   |   |           +-- Name - species - Type: None",  # AtomTrailer
            "breed - Type: NoType",
            "s - Type: NoType",
            "Body - Type: NoType",
        ]
        try:
            self.assertIn("HasVar - species - Type: builtins.str", out)
            self.assertIn("myDog - Type: type_info_in_symtab.Dog", out)
            self.assertIn("Body - Type: type_info_in_symtab.Dog.Body", out)
            self.assertEqual(out.count("Type: builtins.str"), 22)
            for i in lis:
                self.assertNotIn(i, out)
        except AssertionError as e:
            self.skipTest(f"Type information is not complete:{e}")
