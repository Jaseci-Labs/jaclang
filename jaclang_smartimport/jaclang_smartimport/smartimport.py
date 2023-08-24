import importlib
import inspect
import multiprocessing
import os
import logging
import sys
from typing import Optional
import types

logging.basicConfig(level=logging.INFO)


class ModuleLoader:
    def __init__(self):
        self.loaded_modules = {}
        self.processes = {}

    def __call__(self, module_name):
        if module_name not in self.loaded_modules:
            queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=self._load_module_subprocess, args=(module_name, queue)
            )
            process.start()

            try:
                logging.info("Waiting for result from subprocess...")
                result = queue.get(timeout=10)
                logging.info(f"Received result from subprocess: {result}")

                if isinstance(result, Exception):
                    raise result

                if result == "success":
                    module = sys.modules[module_name]
                    wrapper = self.ModuleWrapper(module)
                else:
                    raise ImportError(f"Failed to import module {module_name}")

            except multiprocessing.queues.Empty:
                process.terminate()
                raise TimeoutError(
                    f"Failed to load module {module_name} within the timeout period."
                )

            self.loaded_modules[module_name] = wrapper
            self.processes[module_name] = process
            process.join()

        return self.loaded_modules[module_name]

    def unload_module(self, module_name):
        if module_name in self.loaded_modules:
            self.loaded_modules[module_name].valid = False
            process = self.processes.get(module_name)
            if process and process.is_alive():
                process.terminate()
                logging.info(f"Terminated subprocess for module: {module_name}")
            del self.loaded_modules[module_name]
            del self.processes[module_name]

    def _load_module_subprocess(self, module_name, queue):
        try:
            logging.info(f"Subprocess PID: {os.getpid()}")
            importlib.import_module(module_name)
            logging.info(f"Successfully imported {module_name} in subprocess.")
            queue.put("success")
        except Exception as e:
            logging.error(f"Error importing {module_name} in subprocess: {e}")
            queue.put(e)

    class ModuleWrapper:
        def __init__(self, module):
            self.module = module
            self.valid = True
            self._module_info = None

        def __getattr__(self, attr_name):
            self._check_validity()
            if attr_name == "__module_info__":
                return self.get_entities_info()
            return getattr(self.module, attr_name)

        def __setattr__(self, attr_name, value):
            if attr_name in ["module", "valid", "_module_info"]:
                super().__setattr__(attr_name, value)
            else:
                setattr(self.module, attr_name, value)

        def get_entities_info(self):
            if self._module_info is None:
                self._module_info = {}
                for name, entity in inspect.getmembers(self.module):
                    self._module_info[name] = type(entity).__name__
            return self._module_info

        def __call__(self, entity_name, *args, **kwargs):
            self._check_validity()
            entity = getattr(self.module, entity_name, None)
            if not entity:
                raise AttributeError(
                    f"'{entity_name}' not found in module '{self.module.__name__}'"
                )
            if not callable(entity):
                raise TypeError(f"'{entity_name}' is not callable")
            return entity(*args, **kwargs)

        def _check_validity(self):
            if not self.valid:
                raise Exception(
                    "This module has been unloaded and is no longer accessible."
                )


def jac_red_import_override(
    target: str, base_path: Optional[str] = None, save_file: bool = False
) -> Optional[types.ModuleType]:
    """Override for Jac Red Imports using ModuleLoader."""
    loader = ModuleLoader()
    module = loader(target)
    return module
