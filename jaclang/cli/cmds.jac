"""
This is the implementation of the command line interface tool for the
Jac language. It's built with the Jac language via bootstraping and
represents the first such production Jac program.
"""
import:jac from cli, cmd_registry as cmd_reg;

include:jac impl.cmds_impl;

@cmd_reg.register
can load(filename: str);