"""Test Jac Plugins."""

import subprocess

from jac_streamlit import AppTest

from jaclang.utils.test import TestCase


class JacStreamlitPlugin(TestCase):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        return super().setUp()

    def test_streamlit(self) -> None:
        """Basic test for pass."""
        command_streamlit = "jac streamlit -h"
        command_dot_view = "jac dot_view -h"
        result = subprocess.run(
            command_streamlit, shell=True, capture_output=True, text=True
        )
        dot_result = subprocess.run(
            command_dot_view, shell=True, capture_output=True, text=True
        )
        self.assertIn("Streamlit the specified .jac file", result.stdout)
        self.assertIn(
            ":param filename: The path to the .jac file.\n\npositional arguments:\n",
            result.stdout,
        )
        self.assertIn(
            "View the content of a DOT file. in Streamlit Application.",
            dot_result.stdout,
        )

    def test_app(self) -> None:
        """Test Jac Streamlit App."""
        fixture_abs_path = self.fixture_abs_path("sample.jac")
        app: AppTest = AppTest.from_jac_file(fixture_abs_path).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.get("button")[0].label, "Greet me")

        app.get("text_input")[0].set_value("John Doe")
        app.get("number_input")[0].set_value(42)
        app.get("button")[0].set_value(True).run()
        self.assertEqual(app.success[0].value, "Hello, John Doe! You are 42 years old.")
