from jaclang_smartimport import ModuleLoader
import unittest
import sys


class TestSmartImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestSmartImport, cls).setUpClass()
        cls.loader = ModuleLoader()

    def test_get(self):
        math_module = self.loader("math")
        result = math_module.sqrt(4)
        self.assertEqual(result, 2.0)

    def test_call(self):
        math_module = self.loader("math")
        result = math_module.sqrt(9)
        self.assertEqual(result, 3.0)

    def test_module_info(self):
        math_module = self.loader("math")
        info = math_module.__module_info__
        self.assertIn("name", info)
        self.assertIn("doc", info)
        self.assertIn("attributes", info)
        self.assertEqual(info["name"], "math")

    def test_exception(self):
        math_module = self.loader("math")
        with self.assertRaises(AttributeError):
            _ = math_module.non_existent_attribute

    def test_custom_module_functions(self):
        custom_module = self.loader("test_module")

        # Test square function
        result = custom_module.square(4)
        self.assertEqual(result, 16)

        # Test reverse_list function
        reversed_list = custom_module.reverse_list([1, 2, 3])
        self.assertEqual(reversed_list, [3, 2, 1])

    def test_custom_module_exceptions(self):
        custom_module = self.loader("test_module")

        # Test calling function with wrong arguments
        with self.assertRaises(TypeError):
            _ = custom_module.square("invalid_argument")

        # Test accessing non-existent attributes
        with self.assertRaises(AttributeError):
            _ = custom_module.non_existent_function()
        with self.assertRaises(AttributeError):
            _ = custom_module.non_existent_attribute

    def test_custom_module_variables(self):
        custom_module = self.loader("test_module")

        # Test getting global variables
        self.assertEqual(custom_module.my_list, [1, 2, 3, 4, 5])

        # Test modifying global variables
        custom_module.my_list = [1, 2, 3, 4, 5, 6]
        updated_list = custom_module.my_list  # Fetch the updated list
        self.assertEqual(updated_list, [1, 2, 3, 4, 5, 6])

        custom_module.my_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        updated_dict = custom_module.my_dict  # Fetch the updated dict
        self.assertEqual(updated_dict, {"a": 1, "b": 2, "c": 3, "d": 4})

    def test_set(self):
        custom_module = self.loader("test_module")
        with self.assertRaises(
            AttributeError, msg="'test_module' has no attribute 'new_attribute'"
        ):
            custom_module.new_attribute = "test_value"

    def test_main_process_not_imported(self):
        # Ensure math is not in sys.modules before the test
        if "math" in sys.modules:
            del sys.modules["math"]
        self.loader("math")
        self.assertNotIn(
            "math", sys.modules, "'math' unexpectedly found in sys.modules"
        )

    def test_exceptions(self):
        math_module = self.loader("math")
        with self.assertRaises(AttributeError):
            _ = math_module.non_existent_function()
        with self.assertRaises(AttributeError):
            _ = math_module.non_existent_attribute
        with self.assertRaises(TypeError):
            _ = math_module.sqrt("invalid_argument")

    def test_subprocess_termination(self):
        # Load the math module
        math = self.loader("math")
        # Unload the math module
        self.loader.unload_module("math")
        with self.assertRaises(
            ModuleNotFoundError, msg="Module math has been unloaded."
        ):
            math.pi

    @classmethod
    def tearDownClass(cls):
        super(TestSmartImport, cls).tearDownClass()
        cls.loader.unload_module("math")
        cls.loader.unload_module("test_module")
