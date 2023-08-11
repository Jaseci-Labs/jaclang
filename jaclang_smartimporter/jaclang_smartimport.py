import importlib
import inspect
import multiprocessing


class ModuleLoader:
    def __init__(self):
        self.loaded_modules = {}

    def __call__(self, module_name):
        if module_name not in self.loaded_modules:
            module = importlib.import_module(module_name)
            self.loaded_modules[module_name] = self.ModuleWrapper(module)

        return self.loaded_modules[module_name]

    class ModuleWrapper:
        def __init__(self, module):
            self.module = module
            self.namespace = multiprocessing.Manager().Namespace()

        def __getattr__(self, attr_name):
            if attr_name == "__module_info__":
                self._get_entities()
                return self.namespace.__module_info__

            return getattr(self.module, attr_name)

        def __setattr__(self, attr_name, value):
            if attr_name == "__module_info__":
                self.namespace.__module_info__ = value
            else:
                super().__setattr__(attr_name, value)

        def __call__(self, entity_name, *args, **kwargs):
            try:
                entity = getattr(self.module, entity_name)
                result = entity(*args, **kwargs)
                return result
            except Exception as e:
                raise Exception(
                    f"Failed to call entity '{entity_name}' in module '{self.module.__name__}': {str(e)}"  # noqa
                )

        def _get_entities(self):
            try:
                __module_info__ = {}
                for name, entity in inspect.getmembers(self.module):
                    __module_info__[name] = type(entity).__name__

                self.namespace.__module_info__ = __module_info__
            except Exception as e:
                self.namespace.error = str(e)


# # Example usage
# if __name__ == "__main__":

#     # Load the 'math' module
#     loader = ModuleLoader()

#     math = loader("math")
#     print(type(math))
#     entities = math._jac_ent_
#     print(entities)

#     result = math.pow(2, 3)
#     print(result)

#     log = math.log
#     result = log(10)
#     print(result)

#     random = loader("random")

#     entities = random.entities
#     print(entities)

#     print(math.entities)
#     print(math.pi)
#     math.pi = 10
#     print(math.pi)
