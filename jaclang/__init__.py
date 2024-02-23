"""The Jac Programming Language."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

from jaclang.core.importer import general_importer

from jaclang.plugin.default import JacFeatureDefaults  # noqa: E402
from jaclang.plugin.feature import JacFeature, pm  # noqa: E402
from jaclang.vendor import (
    lark,  # noqa: E402
    mypy,  # noqa: E402
    pluggy,  # noqa: E402
)

jac_import = JacFeature.jac_import

__all__ = [
    "jac_import",
    "lark",
    "mypy",
    "pluggy",
]
pm.register(JacFeatureDefaults)
pm.load_setuptools_entrypoints("jac")
