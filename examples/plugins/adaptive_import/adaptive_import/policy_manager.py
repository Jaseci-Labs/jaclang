import json
from .library_monitor import LibraryMonitor
import os
from typing import Dict, Any


class PolicyManager:
    CPU_THRESHOLD = 0.75
    dir_path = os.path.dirname(os.path.realpath(__file__))
    library_data_path = os.path.join(dir_path, "library_data_dict.json")

    def __init__(
        self,
        library_monitor: LibraryMonitor,
        library_data_path=library_data_path,
    ):
        with open(library_data_path, "r") as f:
            self.library_data_dict = json.load(f)

        self.library_monitor = library_monitor
        self.current_placement: Dict = {}

    def get_dependencies(self, module_name: str):
        """
        Retrieves a list of dependencies for the specified module.
        """
        module_data = self.library_data_dict.get(module_name, {})
        return module_data.get("dependency", [])

    def determine_strategy(self, module_name: str) -> tuple[Any, Any | None]:
        """
        Determine the initial strategy for loading the module based on static criteria.
        """
        remote_load_type = None
        if module_name in self.current_placement:
            return self.current_placement[module_name]

        module_data = self.library_data_dict.get(module_name, {})
        strategy = module_data.get("load_type", "local")
        if strategy == "remote":
            remote_load_type = module_data.get("remote_load_type", "shared")
        self.current_placement[module_name] = strategy
        print(
            f"Placement for {module_name}: {strategy}, remote_load_type: {remote_load_type}"
        )
        return strategy, remote_load_type

    async def adapt_module_placement(self, module_name: str):
        """
        Dynamically adjust the loading strategy based on real-time usage metrics.
        """
        await self.library_monitor.fetch_node_available_resources()
        await self.library_monitor.fetch_module_resources(module_name)

        module_resources = self.library_monitor.module_resources.get(module_name, {})
        node_resources = self.library_monitor.node_resources
        if (module_resources["cpu"] <= node_resources["cpu"]) * self.CPU_THRESHOLD and (
            module_resources["memory"] <= node_resources["memory"]
        ):
            strategy = "shared"
        else:
            strategy = "isolated"

        self.current_placement[module_name] = strategy
        print(f"Placement for {module_name}: {strategy}")
        return strategy

    def get_placement(self, module_name: str):
        """
        Returns the current placement for the given module, adjusting it if necessary.
        """
        if module_name not in self.current_placement:
            self.determine_strategy(module_name)

        return self.adapt_module_placement(module_name)
