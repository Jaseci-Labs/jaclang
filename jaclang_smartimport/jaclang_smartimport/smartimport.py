from typing import Optional
import types
import importlib
import multiprocessing
import logging
import queue

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more detailed logging


class ModuleLoader:
    def __init__(self):
        self.modules_data = {}
        self.proxy = None

    def __call__(self, module_name):
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
                raise ImportError(
                    f"Failed to import module {module_name}: {startup_status}"
                )

        return self.modules_data[module_name][0]

    def unload_module(self, module_name):
        if module_name in self.modules_data:
            _, process = self.modules_data[module_name]
            process.terminate()
            logging.info(f"Terminated subprocess for module: {module_name}")
            self.proxy.is_alive = False
            del self.modules_data[module_name]

    def _load_module_subprocess(self, module_name, command_queue, response_queue):
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
                    func = getattr(module, func_name)
                    result = func(*func_args, **func_kwargs)
                    response_queue.put(result)
                elif operation == "info":
                    info = {
                        "name": module_name,
                        "doc": module.__doc__,
                        "attributes": dir(module),
                    }
                    response_queue.put(info)
        except Exception as e:
            logging.error(f"Error in subprocess for module {module_name}: {e}")
            response_queue.put(str(e))

    class ModuleProxy:
        def __init__(self, module_name, command_queue, response_queue):
            self.module_name = module_name
            self.command_queue = command_queue
            self.response_queue = response_queue
            self.is_alive = True

        def __getattr__(self, attr_name):

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

        def __setattr__(self, attr_name, value):
            # Directly set the attributes for internal attributes to avoid recursion
            if attr_name in [
                "module_name",
                "command_queue",
                "response_queue",
                "is_alive",
            ]:
                self.__dict__[attr_name] = value
            else:
                self.command_queue.put(("set", attr_name, value))
                result = self.response_queue.get()
                if isinstance(result, Exception):
                    raise result


def jac_red_import_override(
    target: str, base_path: Optional[str] = None, save_file: bool = False
) -> Optional[types.ModuleType]:
    """Override for Jac Red Imports using ModuleLoader."""
    loader = ModuleLoader()
    return loader(target)
