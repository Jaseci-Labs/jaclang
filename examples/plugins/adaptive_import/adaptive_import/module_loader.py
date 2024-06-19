import importlib
from .module_actor import ModuleActor
import ray


class ModuleLoader:
    def __init__(self, policy_manager, use_ray_object_store=False):
        self.policy_manager = policy_manager
        self.remote_modules = {}
        self.use_ray_object_store = use_ray_object_store

    async def load_module(self, module_name):
        strategy, remote_load_type = self.policy_manager.determine_strategy(module_name)
        dependencies_list = self.policy_manager.get_dependencies(module_name)

        if strategy == "local":
            module = self.load_module_locally(module_name)
        else:
            module_actor = ModuleActor.options(name=module_name).remote(
                module_name,
            )
            module = RemoteModuleProxy(
                module_name,
                module_actor,
                use_ray_object_store=True,
            )

        return module

    def load_module_locally(self, module_name):
        return importlib.import_module(module_name)


class RemoteModuleProxy:
    def __init__(self, module_name, actor_handle, use_ray_object_store=False):
        self.module_name = module_name
        self.actor_handle = actor_handle
        self.use_ray_object_store = use_ray_object_store
        self.logger = logging.getLogger(__name__)

    def __getattr__(self, attribute_name):
        new_attribute_path = f"{self.module_name}.{attribute_name}"
        if attribute_name.startswith("__") and attribute_name.endswith("__"):
            # Handle special attributes directly
            raise AttributeError(
                f"{self.module_name} has no attribute {attribute_name}"
            )
        return RemoteAttributeProxy(
            self.module_name,
            self.actor_handle,
            attribute_name,
            use_ray_object_store=self.use_ray_object_store,
        )

    def __repr__(self):
        return f"<RemoteModuleProxy for {self.module_name} at {hex(id(self))}>"


import logging


class RemoteAttributeProxy:
    def __init__(
        self, module_name, actor_handle, attribute_path, use_ray_object_store=False
    ):
        self.module_name = module_name
        self.actor_handle = actor_handle
        self.attribute_path = attribute_path
        self.use_ray_object_store = use_ray_object_store

    def __getattr__(self, attribute_name):
        if attribute_name.startswith("__") and attribute_name.endswith("__"):
            # Handle special attributes directly
            raise AttributeError(
                f"{self.attribute_path} has no attribute {attribute_name}"
            )
        new_attribute_path = f"{self.attribute_path}.{attribute_name}"
        return RemoteAttributeProxy(
            self.module_name,
            self.actor_handle,
            new_attribute_path,
            self.use_ray_object_store,
        )

    def __call__(self, *args, **kwargs):

        result = ray.get(
            self.actor_handle.execute_method.remote(
                self.attribute_path, *args, **kwargs
            )
        )
        # result = {"type": None, "value": None, "id": None}
        # print(f"Result: {result}")
        if result["type"] == "instance":
            return InstanceProxy(self.actor_handle, result["id"])
        return result["value"]

    def __iter__(self):
        raise TypeError(f"{self.attribute_path} is not iterable")

    def __next__(self):
        raise StopIteration


class InstanceProxy:
    def __init__(self, actor_handle, instance_id):
        self.actor_handle = actor_handle
        self.instance_id = instance_id

    def __getattr__(self, method_name):
        def method_proxy(*args, **kwargs):
            result = ray.get(
                self.actor_handle.execute_instance_method.remote(
                    self.instance_id, method_name, *args, **kwargs
                )
            )
            return result

        return method_proxy
