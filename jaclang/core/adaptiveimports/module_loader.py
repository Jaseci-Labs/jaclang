"""Module for loading Python modules in separate Kubernetes pods."""

import logging
from remote_module_proxy import RemoteModuleProxy
from policy_manager import PolicyManager
from library_monitor import LibraryMonitor
import importlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAMESPACE = "smart"


class ModuleLoader:
    """A class responsible for loading Python modules in separate Kubernetes pods."""

    def __init__(
        self, policy_manager: PolicyManager, library_monitor: LibraryMonitor
    ) -> None:
        """Initialize the ModuleLoader."""
        self.modules_data = {}
        self.policy_manager = policy_manager
        self.library_monitor = library_monitor

    async def __call__(self, module_name: str, server_ip: str = None) -> "ModuleLoader":
        """Call the ModuleLoader."""
        if module_name not in self.modules_data:
            await self.load_module(module_name, server_ip=server_ip)
        return self.modules_data[module_name]

    async def load_module(self, module_name: str, server_ip: str = None):
        """Load a module."""
        strategy = self.policy_manager.determine_strategy(module_name)
        if strategy == "local":
            return self.load_module_locally(module_name)
        elif strategy == "remote":
            return await self.load_module_remotely(module_name, server_ip)

    def load_module_locally(self, module_name: str):
        """Load a module locally and handle exceptions more gracefully."""
        try:
            module = importlib.import_module(module_name)
            self.modules_data[module_name] = module
            logger.info(f"Successfully loaded '{module_name}' locally.")
            return module
        except ImportError as e:
            logger.error(f"Module '{module_name}' not found: {e}")
            raise ImportError(
                f"Could not find module '{module_name}'. Please ensure it is installed."
            ) from e
        except Exception as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            raise ImportError(
                f"Failed to load module '{module_name}' due to an unexpected error."
            ) from e

    async def load_module_remotely(
        self, module_name: str, server_ip: str = None
    ) -> "ModuleLoader":
        """Load a module."""
        pod_name = f"{module_name}-server"
        pod_status = self.library_monitor.get_pod_status(pod_name)
        if pod_status == "Running":
            if module_name not in self.modules_data:
                proxy = RemoteModuleProxy(module_name, server_ip=server_ip)
                self.modules_data[module_name] = proxy
            return self.modules_data[module_name]
        created_pod_name = self.library_monitor.create_pod(module_name)
        if created_pod_name:
            await self.library_monitor.wait_for_pod_ready(created_pod_name)
            proxy = RemoteModuleProxy(module_name, server_ip=server_ip)
            self.modules_data[module_name] = proxy
            return proxy
        else:
            # This might involve retrying or falling back to local loading
            return None

    async def unload_module(self, module_name: str) -> None:
        """Unload a module."""
        # Check if the module has a proxy and stop port forwarding
        if module_name in self.modules_data:
            proxy = self.modules_data[module_name]
            await proxy.stop_port_forwarding()  # Ensure this is an async call
            del self.modules_data[module_name]

        pod_name = f"{module_name}-server"
        success = await self.library_monitor.delete_pod(pod_name)
        if success:
            print(f"Successfully unloaded and deleted pod for module {module_name}.")
        else:
            print(
                f"Failed to delete pod for module {module_name}. May already be deleted or never existed."
            )
