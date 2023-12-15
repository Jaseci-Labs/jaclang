"""This sample demonstrates how to use ModuleLoader to load a module."""
import asyncio

from module_loader_sub_pod_v2 import ModuleLoader

smart_import = ModuleLoader()
modules_to_load = ["math", "torch", "transformers"]


async def main() -> None:
    """Load a module using the ModuleLoader class."""
    try:
        math, torch, transformers = await asyncio.gather(
            *(smart_import(module) for module in modules_to_load)
        )
        # Load the 'math' module using the smart_import function
        # math = await smart_import("math")
        # Access module attributes using the plugin
        print(math.pi)
        result = math.pow(2, 3)
        print(result)
        math.pi = 19
        print(math.pi)
        # Access the __module_info__ attribute to get information about entities
        entities_info = math.__module_info__
        print(entities_info)
        # Load the 'torch' module using the smart_import function
        # torch = await smart_import("torch")
        try:
            tensor = torch.tensor([1.0, 2.0, 3.0])
        except Exception as e:
            print(f"Error: {e}")
            if "Missing module dependencies:" in str(e):
                missing_module = str(e).split(":")[1].split(".")[0].strip()
                print(f"Attempting to install {missing_module}...")
                torch.install_missing_module(missing_module)
                tensor = torch.tensor([1.0, 2.0, 3.0])
        # Define a tensor
        print(f"type of value : {type(tensor)}")
        print(tensor)
        print(tensor.tolist())
        # Get the sum of the tensor
        tensor_sum = torch.sum(tensor)
        print(f"Sum of tensor: {tensor_sum}")

        # Check if CUDA is available
        print(torch.cuda.is_available())
        bert_model = transformers.from_pretrained("bert-base-uncased")
        print(bert_model)
    finally:
        # Ensure that all modules are unloaded and subprocesses are terminated
        # await smart_import.unload_module("math")
        # await smart_import.unload_module("torch")
        pass


# Run the asynchronous main function
asyncio.run(main())
