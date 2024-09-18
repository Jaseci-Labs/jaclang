import ray
import importlib
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@ray.remote
class ModuleActor:
    def __init__(self, module_name):

        self.module = importlib.import_module(module_name)
        logger.info(f"Module {self.module.__name__} loaded")
        print(f"Module {self.module.__name__} loaded")
        self.instances = {}

    async def execute_method(self, attribute_path, *args, **kwargs):
        try:
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
                # print(f"Result: {result}")
                import numpy as np

                if isinstance(result, (int, float, str, bool)):
                    return {"type": "primitive", "value": int(result)}
                elif isinstance(result, (list, tuple, np.ndarray)):
                    return {"type": "array", "value": result.tolist()}
                elif isinstance(result, dict):
                    return {"type": "dict", "value": result}
                else:
                    return {"type": "unknown", "value": str(result)}
            else:
                # print(f"Result: {result}")
                return {"type": "result", "value": final_attr}
        except Exception as e:
            logger.error(f"Error executing method {final_attr}: {e}")
            raise e

    async def execute_instance_method(self, instance_id, method_name, *args, **kwargs):
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError("Instance not found")

        method = getattr(instance, method_name)
        result = method(*args, **kwargs)
        return {"type": "result", "value": result}
