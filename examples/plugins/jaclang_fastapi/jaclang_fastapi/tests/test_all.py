"""Temporary."""

from contextlib import suppress
from multiprocessing import Process

from httpx import get

from jaclang.cli import cli
from jaclang.utils.test import TestCase

paths = {
    "/user/register": ["post"],
    "/user/login": ["post"],
    "/walker/post_no_body": ["post"],
    "/walker/post_no_body/{node}": ["post"],
    "/walker/post_with_body": ["post"],
    "/walker/post_with_body/{node}": ["post"],
    "/walker/get_no_body": ["get"],
    "/walker/get_no_body/{node}": ["get"],
    "/walker/get_with_query": ["get"],
    "/walker/get_with_query/{node}": ["get"],
    "/walker/get_all_query": ["get"],
    "/walker/get_all_query/{node}": ["get"],
    "/walker/combination": ["post", "get"],
    "/walker/combination/{node}": ["post", "get"],
    "/walker/post_path_var/{a}": ["post", "get"],
    "/walker/post_path_var/{node}/{a}": ["post", "get"],
    "/walker/combination2/{a}": [
        "post",
        "get",
        "put",
        "patch",
        "delete",
        "head",
        "trace",
        "options",
    ],
    "/walker/combination2/{node}/{a}": [
        "post",
        "get",
        "put",
        "patch",
        "delete",
        "head",
        "trace",
        "options",
    ],
    "/walker/post_with_file": ["post"],
    "/walker/post_with_file/{node}": ["post"],
    "/walker/post_with_body_and_file": ["post"],
    "/walker/post_with_body_and_file/{node}": ["post"],
    "/walker/change_new_girl": ["post"],
    "/walker/change_new_girl/{node}": ["post"],
    "/walker/test_array": ["post"],
    "/walker/test_array/{node}": ["post"],
}


class JacLangFastAPITests(TestCase):
    """Temporary."""

    def setUp(self) -> None:
        """Temporary."""
        self.server = Process(
            target=cli.run,
            args=(self.fixture_abs_path("simple_walkerapi.jac"),),
            daemon=True,
        )
        self.server.start()
        while True:
            with suppress(Exception):
                self.get_openapi_json(1)
                break

        return super().setUp()

    def tearDown(self) -> None:
        """Temporary."""
        self.server.terminate()
        return super().tearDown()

    def get_openapi_json(self, timeout: int = None) -> None:
        """Temporary."""
        return get("http://localhost:8000/openapi.json", timeout=timeout).json()

    def test_all_features(self) -> None:
        """Temporary."""
        res = self.get_openapi_json()

        for path, methods in res["paths"].items():
            self.assertEqual(paths.get(path), list(methods.keys()))
