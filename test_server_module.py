"""Unit tests for the ModuleLoader class in module_loader_sub_pod_v2."""

# Standard library imports
import unittest
from unittest.mock import Mock, patch

# Third-party imports
from module_loader_sub_pod_v2 import ModuleLoader


class TestModuleLoader(unittest.TestCase):
    """Test cases for the ModuleLoader class."""

    @patch("module_loader_sub_pod_v2.kube_client")
    @patch("module_loader_sub_pod_v2.httpx.get")
    def test_module_loader(
        self: "TestModuleLoader", mock_httpx_get: Mock, mock_kube_client: Mock
    ) -> None:
        """Test the behavior of the ModuleLoader with mocked Kubernetes client and httpx.get."""
        mock_pod = Mock()
        mock_pod.status.phase = "Running"
        mock_kube_client.read_namespaced_pod.return_value = mock_pod

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "3.14"}
        mock_httpx_get.return_value = mock_response

        loader = ModuleLoader()
        math = loader("math")
        result = math.pi

        self.assertEqual(result, "3.14")


if __name__ == "__main__":
    unittest.main()
