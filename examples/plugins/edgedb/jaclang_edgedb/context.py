from dataclasses import asdict
from typing import Any, Union
from fastapi import Request

from jaclang.core.construct import Architype


class JacContext:
    """Jac Lang Context Handler."""

    def __init__(self, request: Request) -> None:
        """Create JacContext."""
        self.__mem__ = {}
        self.request = request
        self.reports = []

    def has(self, id: Union[str, str]) -> bool:
        """Check if Architype is existing in memory."""
        return str(id) in self.__mem__

    def get(self, id: Union[str, str], default: object = None) -> object:
        """Retrieve Architype in memory."""
        return self.__mem__.get(str(id), default)

    def set(self, id: Union[str, str], obj: object) -> None:
        """Push Architype in memory via ID."""
        self.__mem__[str(id)] = obj

    def remove(self, id: Union[str, str]) -> object:
        """Pull Architype in memory via ID."""
        return self.__mem__.pop(str(id), None)

    def report(self, obj: Any) -> None:  # noqa: ANN401
        """Append report."""
        self.reports.append(obj)

    def response(self) -> list:
        """Return serialized version of reports."""
        for key, val in enumerate(self.reports):
            if isinstance(val, Architype) and (
                ret_jd := getattr(val, "_jac_doc_", None)
            ):
                self.reports[key] = {**ret_jd.json(), "ctx": asdict(val)}
            else:
                self.clean_response(key, val, self.reports)
        return self.reports

    def clean_response(
        self, key: str, val: Any, obj: Union[list, dict]  # noqa: ANN401
    ) -> None:
        """Cleanup and override current object."""
        if isinstance(val, list):
            for idx, lval in enumerate(val):
                self.clean_response(idx, lval, val)
        elif isinstance(val, dict):
            for key, dval in val.items():
                self.clean_response(key, dval, val)
        elif isinstance(val, Architype):
            addons = {}
            if ret_jd := getattr(val, "_jac_doc_", None):
                addons = ret_jd.json()
            obj[key] = {**addons, "ctx": asdict(val)}
