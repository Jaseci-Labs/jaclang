from __future__ import annotations
from jaclang.plugin.feature import JacFeature as jac


@jac.make_walker(on_entry=[jac.DSFunc("self_destruct", None)], on_exit=[])
class Visitor:
    def self_destruct(self, jac_here_) -> None:
        print("get's here")
        jac.disengage(self)
        return
        print("but not here")


jac.spawn_call(jac.get_root(), Visitor())
