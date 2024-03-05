"""Temporary."""

from contextlib import suppress
from os import getenv
from unittest import TestCase

from httpx import get


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
        self.host = getenv("TEST_HOST", "0.0.0.0")
        count = 0
        while True:
            if count > 5:
                self.get_openapi_json(1)
                break
            else:
                with suppress(Exception):
                    self.get_openapi_json(1)
                    break
            count += 1

        return super().setUp()

    def get_openapi_json(self, timeout: int = None) -> None:
        """Temporary."""
        res = get(f"http://{self.host}:8000/openapi.json", timeout=timeout)
        res.raise_for_status()
        return res.json()

    def test_all_features(self) -> None:
        """Temporary."""
        res = self.get_openapi_json()

        for path, methods in res["paths"].items():
            self.assertEqual(paths.get(path), list(methods.keys()))
