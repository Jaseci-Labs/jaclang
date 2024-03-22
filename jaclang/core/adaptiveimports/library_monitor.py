import kubernetes.client
from kubernetes import client
from kubernetes.client.rest import ApiException
import asyncio
import logging

NAMESPACE = "smart"

import json

# Load the library data from JSON
with open("library_data_dict.json", "r") as f:
    library_data_dict = json.load(f)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LibraryMonitor:
    def __init__(self):
        self.config = kubernetes.client.Configuration()
        self.api_instance = kubernetes.client.CoreV1Api(
            kubernetes.client.ApiClient(self.config)
        )
        self.kube_client = client.CoreV1Api()

    def check_metrics(self, module_name):
        # Assuming the library_data_dict is loaded into this dictionary
        module_data = library_data_dict.get(module_name, {})

        return {
            "memory_required": module_data.get("lib_mem_size_req", "512Mi"),
            "cpu_required": module_data.get("lib_cpu_req", "500m"),
        }

    def parse_memory_string(self, mem_str):
        units = {"Mi": 1024**2, "Gi": 1024**3, "Ki": 1024}
        number, unit = mem_str[:-2], mem_str[-2:]
        return int(number) * units[unit]

    def create_pod(self, module_name: str) -> str:
        pod_manifest = self.build_pod_manifest(module_name)
        pod_name = pod_manifest["metadata"]["name"]
        try:
            self.api_instance.create_namespaced_pod(
                body=pod_manifest, namespace=NAMESPACE
            )
            logger.info(f"Pod {pod_name} created for module {module_name}.")
            return pod_name
        except ApiException as e:
            logger.error(f"Exception when creating pod {pod_name}: {e}")
            return None

    def build_pod_manifest(self, module_name: str) -> dict:
        module_data = library_data_dict.get(module_name, {})
        memory_req = module_data.get("lib_mem_size_req", "512Mi")
        cpu_req = module_data.get("lib_cpu_req", "500m")

        pod_name = f"{module_name}-server"
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name},
            "spec": {
                "containers": [
                    {
                        "name": f"{module_name}-container",
                        "image": module_data.get(
                            "image", "default-module-server-image"
                        ),
                        "args": module_data.get("args", ["/app/startup.sh"]),
                        "env": [{"name": "MODULE_TO_INSTALL", "value": module_name}],
                        "resources": {
                            "requests": {"memory": memory_req, "cpu": cpu_req},
                            "limits": {"memory": memory_req, "cpu": cpu_req},
                        },
                    }
                ]
            },
        }

    async def delete_pod(self, pod_name):
        try:
            # Asynchronously delete the Kubernetes pod
            await self.api_instance.delete_namespaced_pod(
                name=pod_name,
                namespace=NAMESPACE,
                body=client.V1DeleteOptions(),
                async_req=True,
            )
            print(f"Pod {pod_name} deletion initiated.")
            return True
        except client.exceptions.ApiException as e:
            print(f"Exception when deleting pod {pod_name}: {e}")
            return False

    def get_pod_status(self, pod_name):
        try:
            pod = self.api_instance.read_namespaced_pod(pod_name, namespace=NAMESPACE)
            return pod.status.phase
        except ApiException as e:
            if e.status == 404:
                return "Not Found"
            else:
                raise

    async def wait_for_pod_ready(self, pod_name):
        retries = 30  # Number of retries
        delay = 10  # Delay in seconds between retries
        for attempt in range(retries):
            try:
                pod = self.api_instance.read_namespaced_pod(
                    pod_name, namespace=NAMESPACE
                )
                if pod.status.phase == "Running":
                    print(f"Pod {pod_name} is now running.")
                    return True
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    print(f"Pod {pod_name} not found. Waiting for it to be created...")
                else:
                    print(f"Error reading namespaced pod: {e}")
            await asyncio.sleep(delay)
        print(f"Pod {pod_name} did not start after {retries * delay} seconds.")
        return False
