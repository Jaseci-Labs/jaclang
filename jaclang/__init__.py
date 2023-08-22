import logging

from jaclang.jac.importer import (
    handle_jac_error,
    jac_blue_import,
    jac_purple_import,
    jac_red_import as original_jac_red_import,
)
from pkg_resources import DistributionNotFound
import pkg_resources

# Set up logging
logging.basicConfig(level=logging.INFO)

# Attempt to use the plugin's jac_red_import function
try:
    plugin_jac_red_import = pkg_resources.load_entry_point(
        "jaclang_smartimport", "jaclang.plugins", "jac_red_import"
    )
    jac_red_import = plugin_jac_red_import
    logging.info("Successfully loaded the overridden jac_red_import function.")
except (ImportError, DistributionNotFound) as e:
    # Use the original jac_red_import function if the plugin is not installed
    jac_red_import = original_jac_red_import
    logging.error(
        f"Error while trying to load the overridden jac_red_import function: {e}"
    )
    logging.info("Using the original jac_red_import function.")
__all__ = [
    "jac_blue_import",
    "jac_purple_import",
    "handle_jac_error",
    "jac_red_import",
]
