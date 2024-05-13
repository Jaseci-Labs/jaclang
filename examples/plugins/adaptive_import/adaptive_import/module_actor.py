import ray

# from transformers import PreTrainedModel, PreTrainedTokenizer, PreTrainedTokenizerFast
# import numpy as np
import importlib
import uuid


@ray.remote
class ModuleActor:
    def __init__(self, module_name):
        self.module = importlib.import_module(module_name)
        self.instances = {}

    async def execute_method(self, attribute_path, *args, **kwargs):
        attribute = self.module
        path_parts = attribute_path.split(".")
        for attr in path_parts[:-1]:
            attribute = getattr(attribute, attr)

        final_attr = getattr(attribute, path_parts[-1])

        if isinstance(final_attr, type):
            instance = final_attr(*args, **kwargs)
            instance_id = str(uuid.uuid4())
            self.instances[instance_id] = instance
            return {"type": "instance", "id": instance_id}
        elif callable(final_attr):
            result = final_attr(*args, **kwargs)
            return {"type": "result", "value": result}
        else:
            return {"type": "result", "value": final_attr}

    async def execute_instance_method(self, instance_id, method_name, *args, **kwargs):
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError("Instance not found")

        method = getattr(instance, method_name)
        result = method(*args, **kwargs)
        return {"type": "result", "value": result}
