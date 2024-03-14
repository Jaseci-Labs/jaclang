import json

with open("library_data_dict.json", "r") as f:
    library_data_dict = json.load(f)


class PolicyManager:
    def __init__(self, library_monitor):
        self.library_monitor = library_monitor
        self.current_placement = {}

    def determine_strategy(self, module_name):
        """
        Determine if the module should be loaded locally or remotely and return the strategy.
        """
        if module_name in self.current_placement:
            return self.current_placement[module_name]

        strategy = self.initial_load_strategy(module_name)
        self.current_placement[module_name] = strategy
        return strategy

    def initial_load_strategy(self, module_name: str) -> str:
        module_data = library_data_dict.get(module_name, {})
        load_type = module_data.get("load_type", "local")
        return load_type

    def dynamic_load_strategy(self, module_name):
        # In a real scenario, this would be replaced with analysis of real metrics
        usage_pattern = self.library_monitor.get_module_usage_pattern(module_name)
        if usage_pattern == "High Frequency":
            return "local"
        else:
            return "remote"

    def can_load_locally(self, module_name):
        metrics = self.library_monitor.check_metrics(module_name)

        # Placeholder for actual resource check logic
        available_memory = "1Gi"
        available_cpu = "1000m"
        memory_requirement_ok = self.library_monitor.parse_memory_string(
            metrics["memory_required"]
        ) <= self.library_monitor.parse_memory_string(available_memory)
        cpu_requirement_ok = metrics["cpu_required"] <= available_cpu

        return memory_requirement_ok and cpu_requirement_ok

    def monitor_module(self, module_name, threshold):
        # Placeholder method for monitoring module performance and scaling/migrating if necessary
        print(f"Monitoring module {module_name} against threshold {threshold}")

    def adapt_module_placement(self, module_name):
        """
        Decides whether to switch the module from local to remote or vice versa,
        only if there's a change required based on the new strategy.
        """
        new_strategy = self.dynamic_load_strategy(module_name)
        current_placement = self.current_placement.get(module_name, None)

        # Check if a change is needed
        if new_strategy != current_placement:
            if new_strategy == "local":
                # Logic to migrate the module to local (if previously remote)
                print(f"Migrating {module_name} to local due to new strategy.")
                # Placeholder for actual migration logic
                self.current_placement[module_name] = "local"
            elif new_strategy == "remote":
                # Logic to migrate the module to remote
                print(f"Migrating {module_name} to remote due to new strategy.")
                # Placeholder for actual migration logic
                pod_name = self.library_monitor.create_pod(
                    module_name
                )  # Example of deploying to remote
                if pod_name:
                    self.current_placement[module_name] = "remote"
                else:
                    print(f"Failed to migrate {module_name} to remote.")
        else:
            print(
                f"No placement change needed for {module_name}; remains {current_placement}."
            )
