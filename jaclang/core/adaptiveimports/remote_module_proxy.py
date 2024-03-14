import asyncio
import logging
import pickle
import socket
import httpx


def find_available_port() -> int:
    """Find and return an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RemoteModuleProxy:
    """Proxy class for modules."""

    def __init__(self, module_name: str, local_port: int = None, server_ip: str = None):
        self.server_ip = server_ip or "localhost"
        self.local_port = local_port or find_available_port()
        self.module_name = module_name
        self.port_forward_process = None

    async def install_missing_module(self, module_name: str) -> None:
        """Asynchronously install a missing module."""
        async with httpx.AsyncClient() as client:
            try:
                # Asynchronously post a request to install the module
                response = await client.post(
                    f"http://{self.server_ip}:{self.local_port}/install_module/",
                    json={"module_name": module_name},
                )
                response.raise_for_status()
                task_id = response.json().get("task_id")
                print(f"Received task ID: {task_id}")

                while True:
                    status_response = await client.get(
                        f"http://{self.server_ip}:{self.local_port}/install_status/{task_id}/"
                    )
                    status_response.raise_for_status()
                    status = status_response.json().get("status")

                    if status == "completed":
                        print("Installation completed successfully.")
                        break
                    elif status.startswith("error"):
                        print(f"Error during installation: {status}")
                        break

                    await asyncio.sleep(10)
            except httpx.HTTPStatusError as http_status_error:
                print(f"HTTP error occurred: {http_status_error.response.status_code}")
            except httpx.RequestError as request_error:
                print(
                    f"An error occurred while requesting {request_error.request.url!r}."
                )
            except Exception as e:
                print(f"Error while trying to install {module_name}: {e}")

    async def wait_for_server(self, timeout: int = 10) -> bool:
        """Asynchronously wait for the server to be available."""
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://{self.server_ip}:{self.local_port}/health"
                    )
                    if response.status_code == 200:
                        return True
            except httpx.RequestError as e:
                logger.error(f"Waiting for server - Exception: {e}")
            await asyncio.sleep(1)
        return False

    async def start_port_forwarding(self):
        """Start port forwarding using kubectl."""
        cmd = f"kubectl port-forward pod/{self.module_name}-server {self.local_port}:8000 --namespace={NAMESPACE}"
        self.port_forward_process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        server_ready = await self.wait_for_server(timeout=30)
        if server_ready:
            logger.info(
                f"Server is ready to receive requests for module {self.module_name}."
            )
        else:
            logger.error(f"Server did not become ready for module {self.module_name}.")

    async def stop_port_forwarding(self):
        """Stop port forwarding."""
        if self.port_forward_process:
            self.port_forward_process.terminate()
            await self.port_forward_process.wait()
            self.port_forward_process = None
            logger.info(f"Stopped port forwarding for module {self.module_name}")

    async def __getattr__(self, attr_name: str):
        """Asynchronously get an attribute."""
        if attr_name in ["port_forward_process", "local_port"]:
            return getattr(self, attr_name)

        if not self.port_forward_process:
            await self.start_port_forwarding()

        try:
            request_url = f"http://{self.server_ip}:{self.local_port}/{self.module_name}/{attr_name}"
            async with httpx.AsyncClient() as client:
                response = await client.get(request_url)
                response.raise_for_status()

                # Handle different response types
                if response.headers["Content-Type"] == "application/octet-stream":
                    return pickle.loads(response.content)
                else:
                    return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error accessing attribute '{attr_name}': {e}")
            raise AttributeError(
                f"Remote attribute '{attr_name}' could not be retrieved."
            ) from e

    # def __setattr__(self: "RemoteModuleProxy", attr_name: str, value: any) -> None:
    #     """Set an attribute."""
    #     if attr_name in ["module_name", "port_forward_process", "local_port"]:
    #         self.__dict__[attr_name] = value
    #         return
    #     try:
    #         url = f"http://{self.server_ip}:{self.local_port}/{attr_name}"
    #         response = httpx.post(url, json={"value": str(value)})
    #         response.raise_for_status()
    #     except httpx.ConnectError as e:
    #         raise AttributeError(f"Error while setting attribute '{attr_name}': {e}")
