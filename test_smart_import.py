from jaclang_smartimport import (
    ModuleLoader,
)
import unittest


class TestSmartImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestSmartImport, cls).setUpClass()
        cls.loader = ModuleLoader()

    def test_get(self):
        math_module = self.loader("math")
        result = math_module.sqrt(4)
        self.assertEqual(result, 2.0)

    def test_set(self):
        math_module = self.loader("math")
        math_module.new_attribute = "test_value"
        self.assertEqual(math_module.new_attribute, "test_value")

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

    # def test_sub_module_is_active(self):
    #     os_module = self.loader("os.path")
    #     result = os_module.exists(".")
    #     self.assertTrue(result)

    @classmethod
    def tearDownClass(cls):
        super(TestSmartImport, cls).tearDownClass()
        cls.loader.unload_module("math")
