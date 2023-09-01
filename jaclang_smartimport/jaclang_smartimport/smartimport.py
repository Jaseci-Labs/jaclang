"""Provide a mechanism to load Python modules in separate processes."""
import importlib
import logging
import multiprocessing
import queue
import types
from typing import Optional

logging.basicConfig(level=logging.INFO)


class ModuleLoader:
    """A class responsible for loading Python modules in separate processes."""

    def __init__(self: "ModuleLoader") -> None:
        """Initialize the ModuleLoader instance."""
        self.modules_data = {}
        self.proxy = None

    def __call__(self: "ModuleLoader", module_name: str) -> "ModuleProxy":
        """Load the specified module."""
        if module_name not in self.modules_data:
            command_queue = multiprocessing.Queue()
            response_queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=self._load_module_subprocess,
                args=(module_name, command_queue, response_queue),
            )
            process.start()

            self.proxy = self.ModuleProxy(module_name, command_queue, response_queue)
            self.modules_data[module_name] = (self.proxy, process)

            # Check for any startup errors
            startup_status = response_queue.get()
            if startup_status != "success":
                logging.error(
                    f"Error while starting subprocess for module {module_name}: {startup_status}"  # noqa
                )
                raise ImportError(
                    f"Failed to import module {module_name}: {startup_status}"
                )

        return self.modules_data[module_name][0]

    def unload_module(self: "ModuleLoader", module_name: str) -> None:
        """Load the module in a subprocess."""
        if module_name in self.modules_data:
            _, process = self.modules_data[module_name]
            process.terminate()
            logging.info(f"Terminated subprocess for module: {module_name}")
            self.proxy.is_alive = False
            del self.modules_data[module_name]

    def _load_module_subprocess(
        self: "ModuleLoader",
        module_name: str,
        command_queue: multiprocessing.Queue,
        response_queue: multiprocessing.Queue,
    ) -> None:
        """Load the module in a subprocess."""
        try:
            module = importlib.import_module(module_name)
            logging.debug(f"Successfully loaded module {module_name} in subprocess.")
            response_queue.put("success")

            while True:
                operation, *args = command_queue.get()
                if operation == "get":
                    attr_name = args[0]
                    target_module = module
                    for sub_module in attr_name.split(".")[1:-1]:
                        target_module = getattr(target_module, sub_module, None)
                        if not target_module:
                            break

                    if hasattr(target_module, attr_name.split(".")[-1]):
                        attr = getattr(target_module, attr_name.split(".")[-1])
                        if isinstance(attr, types.ModuleType):
                            response_queue.put("module_object")
                        else:
                            response_queue.put(attr)
                    else:
                        logging.debug(f"Attribute {attr_name} not found")
                        response_queue.put(
                            AttributeError(
                                f"'{module_name}' has no attribute '{attr_name}'"
                            )
                        )

                elif operation == "set":
                    attr_name, value = args
                    setattr(module, attr_name, value)
                    response_queue.put("success")
                elif operation == "call":
                    func_name, func_args, func_kwargs = args
                    if hasattr(module, func_name):  # Check if method exists
                        func = getattr(module, func_name)
                        result = func(*func_args, **func_kwargs)
                        response_queue.put(result)
                    else:
                        logging.debug(f"Method {func_name} not found")
                        response_queue.put(
                            AttributeError(
                                f"'{module_name}' has no method '{func_name}'"
                            )
                        )
                elif operation == "info":
                    info = {
                        "name": module_name,
                        "doc": module.__doc__,
                        "attributes": dir(module),
                    }
                    response_queue.put(info)
                elif operation == "exception":
                    # Handle the exception command and continue execution
                    continue
        except Exception as e:
            logging.exception(f"Error in subprocess for module {module_name}.")
            response_queue.put(str(e))

    class ModuleProxy:
        """Initialize the ModuleProxy instance."""

        def __init__(
            self: "ModuleLoader.ModuleProxy",
            module_name: str,
            command_queue: multiprocessing.Queue,
            response_queue: multiprocessing.Queue,
        ) -> None:
            """Initialize the ModuleProxy with the given module name and queues."""
            self.module_name = module_name
            self.command_queue = command_queue
            self.response_queue = response_queue
            self.is_alive = True

        def __getattr__(
            self: "ModuleLoader.ModuleProxy", attr_name: str
        ) -> types.ModuleType:
            """Retrieve the specified attribute from the module."""
            if not self.is_alive:
                raise ModuleNotFoundError(
                    f"Module {self.module_name} has been unloaded."
                )
            if attr_name == "__module_info__":
                self.command_queue.put(("info",))
                result = self.response_queue.get()
                if isinstance(result, Exception):
                    raise result
                return result
            if attr_name.startswith("_"):
                return super().__getattr__(attr_name)
            full_attr_name = f"{self.module_name}.{attr_name}"
            self.command_queue.put(("get", full_attr_name))

            try:
                result = self.response_queue.get(timeout=1)  # 1 second timeout
            except queue.Empty:
                raise ModuleNotFoundError(
                    f"Failed to communicate with subprocess for module {self.module_name}."  # noqa
                )

            if isinstance(result, Exception):
                raise result
            elif result == "module_object":
                return ModuleLoader.ModuleProxy(
                    full_attr_name, self.command_queue, self.response_queue
                )
            return result

        def __setattr__(
            self: "ModuleLoader.ModuleProxy", attr_name: str, value: types.ModuleType
        ) -> None:
            """Set the specified attribute for the module."""
            # Directly set the attributes for internal attributes to avoid recursion
            if attr_name in [
                "module_name",
                "command_queue",
                "response_queue",
                "is_alive",
            ]:
                self.__dict__[attr_name] = value
            else:
                # Check if attribute exists before setting
                if hasattr(self, attr_name):
                    self.command_queue.put(("set", attr_name, value))
                    result = self.response_queue.get()
                    if isinstance(result, Exception):
                        # Send an exception command to the subprocess
                        self.command_queue.put(("exception",))
                        raise result
                else:
                    # Send an exception command to the subprocess
                    self.command_queue.put(("exception",))
                    raise AttributeError(
                        f"'{self.module_name}' has no attribute '{attr_name}'"
                    )


def jac_red_import_override(
    target: str, base_path: Optional[str] = None, save_file: bool = False
) -> Optional[types.ModuleType]:
    """Override for Jac Red Imports using ModuleLoader."""
    loader = ModuleLoader()
    return loader(target)
