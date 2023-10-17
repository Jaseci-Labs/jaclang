"""Module for loading Python modules in separate Kubernetes pods."""

import asyncio
import functools
import logging
import pickle
import socket
import subprocess
import time

import httpx

from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    config.load_incluster_config()
except config.ConfigException:
    try:
        config.load_kube_config()
    except config.ConfigException:
        raise RuntimeError("Could not load Kubernetes configuration")
kube_client = client.CoreV1Api()

NAMESPACE = "default"


class ModuleLoader:
    """A class responsible for loading Python modules in separate Kubernetes pods."""

    def __init__(self) -> None:
        """Initialize the ModuleLoader."""
        self.modules_data = {}

    async def __call__(self, module_name: str, server_ip: str = None) -> "ModuleLoader":
        """Call the ModuleLoader."""
        if module_name not in self.modules_data:
            await self.load_module(module_name, server_ip=server_ip)
        return self.modules_data[module_name]

    async def load_module(
        self, module_name: str, server_ip: str = None
    ) -> "ModuleLoader":
        """Load a module."""
        pod_name = f"{module_name}-server"
        try:
            pod = kube_client.read_namespaced_pod(pod_name, namespace=NAMESPACE)
            if pod.status.phase == "Running":
                if module_name not in self.modules_data:
                    proxy = self.ModuleProxy(module_name, server_ip=server_ip)
                    self.modules_data[module_name] = proxy
                return self.modules_data[module_name]
        except client.exceptions.ApiException as e:
            if e.status != 404:
                logging.error(f"Error reading namespaced pod: {e}")

        # If not, create the pod
        pod_spec = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name=f"{module_name}-container",
                        image="ashishmahendra/module-server:latest",
                        args=["/app/startup.sh"],
                        image_pull_policy="Always",
                        env=[
                            client.V1EnvVar(name="MODULE_TO_INSTALL", value=module_name)
                        ],
                    )
                ]
            ),
        )

        kube_client.create_namespaced_pod(body=pod_spec, namespace=NAMESPACE)

        # Introduce a timeout for waiting for the pod to be in the "Running" state
        retries = 30  # Number of retries
        delay = 10  # Delay in seconds between retries
        for _ in range(retries):
            try:
                pod = kube_client.read_namespaced_pod(pod_name, namespace=NAMESPACE)
                if pod.status.phase == "Running":
                    break
            except client.exceptions.ApiException as e:
                logging.error(f"Error reading namespaced pod: {e}")
            await asyncio.sleep(delay)
        else:
            logging.error(
                f"Pod {pod_name} did not start after {retries * delay} seconds."
            )
            return

        # Create a proxy for the module
        proxy = self.ModuleProxy(module_name, server_ip=server_ip)
        self.modules_data[module_name] = proxy

    class ModuleProxy:
        """Proxy class for modules."""

        def __init__(
            self: "ModuleLoader.ModuleProxy",
            module_name: str,
            local_port: int = None,
            server_ip: str = None,
        ) -> None:
            """Initialize the ModuleProxy."""
            self.__dict__["server_ip"] = server_ip or "localhost"
            if local_port:
                self.__dict__["local_port"] = local_port
            else:
                self.__dict__["local_port"] = find_available_port()
            self.__dict__["module_name"] = module_name
            self.__dict__["port_forward_process"] = None if not local_port else True

        def install_missing_module(
            self: "ModuleLoader.ModuleProxy", module_name: str
        ) -> None:
            """Install a missing module."""
            try:
                response = httpx.post(
                    f"http://{self.server_ip}:{self.local_port}/install_module/",
                    json={"module_name": module_name},
                )
                task_id = response.json().get("task_id")
                print(f"Received task ID: {task_id}")  # Add logging
                # Wait for the installation to complete

                while True:
                    status_response = httpx.get(
                        f"http://{self.server_ip}:{self.local_port}/install_status/{task_id}/"  # noqa
                    )
                    status = status_response.json().get("status")
                    if status == "completed":
                        break
                    elif status.startswith("error"):
                        print(f"Error during installation: {status}")
                        break
                    time.sleep(10)  # Wait for 10 seconds before checking again
            except Exception as install_e:
                print(f"Error while trying to install {module_name}: {install_e}")

        def wait_for_server(
            self: "ModuleLoader.ModuleProxy", timeout: int = 10
        ) -> bool:
            """Wait for the server to be available."""
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = httpx.get(
                        f"http://localhost:{self.local_port}/health", timeout=timeout
                    )
                    if response.status_code == 200:
                        return True
                except Exception as e:  # Catch all exceptions
                    print(f"Exception: {e}")  # Print the exception
                time.sleep(1)
            return False

        def start_port_forwarding(self: "ModuleLoader.ModuleProxy") -> None:
            """Start port forwarding."""
            max_retries = 10
            retry_delay = 10  # seconds
            for _ in range(max_retries):
                try:
                    cmd = [
                        "kubectl",
                        "port-forward",
                        f"pod/{self.module_name}-server",
                        f"{self.local_port}:8000",
                        f"--namespace={NAMESPACE}",
                    ]
                    self.port_forward_process = subprocess.Popen(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    time.sleep(1)
                    if self.wait_for_server():
                        break
                except Exception as e:
                    print(f"Error: {e}")
                time.sleep(retry_delay)

        def stop_port_forwarding(self: "ModuleLoader.ModuleProxy") -> None:
            """Stop port forwarding."""
            if self.port_forward_process:
                self.port_forward_process.terminate()

        def __getattr__(self: "ModuleLoader.ModuleProxy", attr_name: str) -> any:
            """Get an attribute."""
            if attr_name in ["port_forward_process", "local_port"]:
                return self.__dict__.get(attr_name)
            if not self.port_forward_process:
                self.start_port_forwarding()
            try:
                # Construct the request URL using the full module path
                request_url = f"http://{self.server_ip}:{self.local_port}/{self.module_name}/{attr_name}"  # noqa
                response = httpx.get(request_url)
                response.raise_for_status()

                # Try to unpickle the response content directly
                try:
                    response_data = pickle.loads(response.content)
                except Exception:
                    # If unpickling fails, try to interpret it as JSON
                    response_data = response.json()
                if response_data.get("status") == "error":
                    if "PyTorch" in response_data.get("message"):
                        self.install_missing_module("torch")
                        return self.__getattr__(attr_name)
                    else:
                        raise ImportError(response_data.get("message"))

                if "module" in response_data.get("result", ""):
                    full_module_path = f"{self.module_name}.{attr_name}"
                    module_proxy = type(self)(
                        full_module_path, local_port=self.local_port
                    )
                    return module_proxy
                elif response_data.get("type") == "class":
                    # Return a new instance of the ModuleProxy for the class
                    class_module_path = f"{self.module_name}.{attr_name}"
                    return type(self)(class_module_path, local_port=self.local_port)

                elif response_data.get("type") in ["function", "classmethod"]:
                    # Return a callable that makes an HTTP request to execute the function or class method # noqa
                    def remote_callable(
                        module_name: str,
                        server_ip: str,
                        local_port: int,
                        attr_name: str,
                        *args: any,
                        **kwargs: any,
                    ) -> any:
                        """Remote callable."""
                        pickled_data = pickle.dumps({"args": args, "kwargs": kwargs})
                        request_url = f"http://{server_ip}:{local_port}/{module_name}/{attr_name}/execute"  # noqa
                        exec_response = httpx.post(
                            request_url,
                            content=pickled_data,
                        )
                        if exec_response.status_code != 200:
                            print(
                                f"Server returned an error: {exec_response.status_code} - {exec_response.text}"  # noqa
                            )
                            return

                        # Check the Content-Type header
                        content_type = exec_response.headers.get("Content-Type")
                        if content_type == "application/octet-stream":
                            # If the content is pickled, unpickle it
                            response_data = pickle.loads(exec_response.content)
                            return response_data.get("result")
                        else:
                            # Otherwise, interpret the response content as JSON
                            response_data = exec_response.json()
                            if "result" in response_data:
                                return response_data["result"]
                            elif "missing_modules" in response_data:
                                missing_modules = ", ".join(
                                    response_data["missing_modules"]
                                )
                                raise Exception(
                                    f"Missing module dependencies: {missing_modules}. Consider installing them."  # noqa
                                )
                            else:
                                raise Exception(
                                    response_data.get(
                                        "detail", "Unknown error from server"
                                    )
                                )

                    bound_remote_callable = functools.partial(
                        remote_callable,
                        self.module_name,
                        self.server_ip,
                        self.local_port,
                        attr_name,
                    )
                    return bound_remote_callable
                else:
                    return response_data.get("result")
            except httpx.RequestError as e:
                raise AttributeError(
                    f"Error while accessing attribute '{attr_name}': {e}"
                )

        def __setattr__(
            self: "ModuleLoader.ModuleProxy", attr_name: str, value: any
        ) -> None:
            """Set an attribute."""
            if attr_name in ["module_name", "port_forward_process", "local_port"]:
                self.__dict__[attr_name] = value
                return
            try:
                url = f"http://{self.server_ip}:{self.local_port}/{attr_name}"
                response = httpx.post(url, json={"value": str(value)})
                response.raise_for_status()
            except httpx.ConnectError as e:
                raise AttributeError(
                    f"Error while setting attribute '{attr_name}': {e}"
                )

    def unload_module(self: "ModuleLoader", module_name: str) -> None:
        """Unload a module."""
        pod_name = f"{module_name}-server"
        kube_client.delete_namespaced_pod(pod_name, namespace=NAMESPACE)
        if module_name in self.modules_data:
            self.modules_data[module_name].stop_port_forwarding()
            del self.modules_data[module_name]


def find_available_port() -> int:
    """Find and return an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
