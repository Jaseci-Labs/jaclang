"""Module for loading Python modules in separate Kubernetes pods."""

import pickle
import socket
import subprocess
import time

import httpx

from kubernetes import client, config

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

    def __init__(self: "ModuleLoader") -> None:
        """Initialize the ModuleLoader."""
        self.modules_data = {}

    def __call__(
        self: "ModuleLoader", module_name: str, server_ip: str = None
    ) -> "ModuleLoader.ModuleProxy":
        """Call method to load a module."""
        if module_name not in self.modules_data:
            self.load_module(module_name, server_ip=server_ip)
        return self.modules_data[module_name]

    def load_module(
        self: "ModuleLoader", module_name: str, server_ip: str = None
    ) -> None:
        """Load a module."""
        pod_name = f"{module_name}-server"
        try:
            pod = kube_client.read_namespaced_pod(pod_name, namespace=NAMESPACE)
            if pod.status.phase == "Running":
                if module_name not in self.modules_data:
                    proxy = self.ModuleProxy(module_name, server_ip=server_ip)
                    self.modules_data[module_name] = proxy
                return self.modules_data[module_name]
        except client.exceptions.ApiException:
            pass

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

        while True:
            pod = kube_client.read_namespaced_pod(pod_name, namespace=NAMESPACE)
            if pod.status.phase == "Running":
                break
            time.sleep(1)

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
                    f"http://{self.server_ip}:{self.local_port}/install_dependency/",
                    json={"module_name": module_name},
                )
                if response.status_code == 200:
                    if response.json().get("status") == "success":
                        print(f"Successfully installed {module_name}")
                    else:
                        print(
                            f"Failed to install {module_name}. Reason: {response.text}"
                        )
            except Exception as install_e:
                print(f"Error while trying to install {module_name}: {install_e}")

        def wait_for_server(
            self: "ModuleLoader.ModuleProxy", timeout: int = 20
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
            max_retries = 5
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
                request_url = f"http://{self.server_ip}:{self.local_port}/{self.module_name}/{attr_name}"
                response = httpx.get(request_url)
                response.raise_for_status()

                # Try to unpickle the response content directly
                try:
                    response_data = pickle.loads(response.content)
                except Exception:
                    # If unpickling fails, try to interpret it as JSON
                    response_data = response.json()

                if "module" in response_data.get("result", ""):
                    full_module_path = f"{self.module_name}.{attr_name}"
                    module_proxy = type(self)(
                        full_module_path, local_port=self.local_port
                    )
                    return module_proxy
                elif response_data.get("type") == "function":
                    # Return a callable that makes an HTTP request to execute the function
                    def remote_function(
                        self: "ModuleLoader.ModuleProxy", *args: any, **kwargs: any
                    ) -> any:
                        pickled_data = pickle.dumps({"args": args, "kwargs": kwargs})
                        exec_response = httpx.post(
                            f"http://{self.server_ip}:{self.local_port}/{self.module_name}/{attr_name}/execute",
                            content=pickled_data,
                        )
                        if exec_response.status_code != 200:
                            print(
                                f"Server returned an error: {exec_response.status_code} - {exec_response.text}"
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
                                    f"Missing module dependencies: {missing_modules}. Consider installing them."
                                )
                            else:
                                raise Exception(
                                    response_data.get(
                                        "detail", "Unknown error from server"
                                    )
                                )

                    return remote_function
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
