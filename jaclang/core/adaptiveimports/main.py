import asyncio
from library_monitor import LibraryMonitor
from policy_manager import PolicyManager
from module_loader import ModuleLoader


async def main():

    library_monitor = LibraryMonitor()
    policy_manager = PolicyManager(library_monitor)

    module_loader = ModuleLoader(policy_manager, library_monitor)
    module_name = "math"
    module = await module_loader(module_name)
    print(module.pi)


if __name__ == "__main__":
    asyncio.run(main())
