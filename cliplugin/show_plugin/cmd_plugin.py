from jaclang.plugin.default import hookimpl


class JacCliImpl:
    """Jac CLI."""

    @staticmethod
    @hookimpl
    def gr():
        print("hiiiiiiiii-----------------")
