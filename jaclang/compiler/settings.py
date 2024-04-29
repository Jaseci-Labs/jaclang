"""
settings infrastructure that can pull settings from the command line, configuration files.

and environment variables.
"""

import configparser
import os


class Settings:
    """
    A class for managing configuration settings.

    loading them from config.ini and providing programmatic access.
    """

    def __init__(self) -> None:
        """Initialize the Settings object."""
        self.config: dict = {}
        self.load_config_file()

    def load_config_file(self) -> None:
        """Load settings from the config.ini file."""
        currrent_path = os.path.dirname(__file__)
        config_path = os.path.join(currrent_path, "config.ini")
        configs = configparser.ConfigParser()
        if os.path.exists(config_path):
            configs.read(config_path)
            self.config.update(
                {
                    key: self.convert_type(value)
                    for key, value in configs["JAC_OS_ENV_VAR"].items()
                }
            )
        else:
            print("Warning: Config file not found, using default settings.")

    def convert_type(self, value: str) -> str:
        """Convert the configuration value to its appropriate type."""
        if value.lower() == "true":
            return True  # type:ignore
        elif value.lower() == "false":
            return False  # type:ignore
        elif value.isdigit():
            return int(value)  # type:ignore
        return value

    def __getitem__(self, item: str) -> str:
        """Allow accessing settings using dictionary-like syntax."""
        return self.config.get(item)  # type:ignore

    def __repr__(self) -> str:
        """Return a string representation of the Settings object."""
        return f"Settings({self.config})"
