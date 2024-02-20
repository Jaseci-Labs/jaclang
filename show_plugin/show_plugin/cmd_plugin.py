from jaclang.plugin.default import hookimpl
#from jaclang.cli.cmdreg import CommandRegistry
from jaclang.cli.cli import cmd_registry
class JacCliFeature:
    """Jac CLI."""

    @staticmethod
    @hookimpl
    @cmd_registry.register
    def gr():
        print("hiiiiiiiii-----------------inside__plugin-----------------2")
