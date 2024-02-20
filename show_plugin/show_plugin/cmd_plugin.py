from jaclang.plugin.default import hookimpl


class JacCliFeature:
    """Jac CLI."""

    @staticmethod
    @hookimpl
    def gr():
        print("hiiiiiiiii-----------------inside__plugin-----------------2")
