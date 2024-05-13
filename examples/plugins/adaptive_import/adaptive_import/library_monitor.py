# from prometheus_api_client import PrometheusConnect
PROMETHEUS_URL = "http://localhost:8080"


class LibraryMonitor:
    def __init__(self, prometheus_url=PROMETHEUS_URL):
        # self.prometheus = PrometheusConnect(url=prometheus_url)
        self.node_resources = {"cpu": 0, "memory": 0}
        self.module_resources = {}

    async def fetch_node_available_resources(self):
        # Implement actual Prometheus queries here
        self.node_resources["cpu"] = 4
        self.node_resources["memory"] = 8 * 1024**3

    async def fetch_module_resources(self, module_name):
        # Implement actual Prometheus queries here
        self.module_resources[module_name] = {
            "cpu": 2,
            "memory": 2 * 1024**3,
        }

    # def get_cpu_utilization(self, instance_id=None):
    #     """
    #     Get CPU utilization for a specific instance or for all instances.
    #     """
    #     query = "ray_node_cpu_utilization"
    #     if instance_id:
    #         query += f'{{InstanceId="{instance_id}"}}'
    #     print(f"Query: {query}")
    #     result = self.prometheus.custom_query(query)
    #     return result

    # def get_memory_usage(self, instance_id=None):
    #     """
    #     Get memory usage for a specific instance or for all instances.
    #     """
    #     query = "ray_node_mem_used"
    #     if instance_id:
    #         query += f'{{InstanceId="{instance_id}"}}'
    #     result = self.prometheus.custom_query(query)
    #     return result
