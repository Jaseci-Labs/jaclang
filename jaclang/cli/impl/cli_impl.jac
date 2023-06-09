"""Implemenation for Jac's command line interface."""

:o:Command:a:init(func: callable) {
    <s>.func = func;
    <s>.sig = func |> inspect.signature;
}

:o:Command:a:call(*args: list, **kwargs: dict) {
    return (*args, **kwargs) |> <s>.func;
}

:o:CommandRegistry:a:init {
    <s>.registry = {};
    <s>.parser = (prog="CLI") |> argparse.ArgumentParser;
    <s>.sub_parsers =
        (title="commands", dest="command") |> <s>.parser.add_subparsers;
}

:o:CommandRegistry:a:register(func: callable) {
    name = func.__name__;
    cmd = func |> Command;
    <s>.registry[name] = cmd;
    cmd_parser = name |> <s>.sub_parsers.add_parser;
    for param_name, param in |> cmd.sig.parameters.items {
        if param.default is param.empty {
            (f"-{param_name[:1]}", f"--{param_name}",
            required=True, type=param.annotation|>eval)
                |> cmd_parser.add_argument;
        }
        else {
            (f"-{param_name[:1]}", f"--{param_name}",
            default=param.default, type=param.annotation|>eval)
                |> cmd_parser.add_argument;
        }
    }
    return func;
}

:o:CommandRegistry:a:get(name: str) -> Command {
    return name |> <s>.registry.get;
}

:o:CommandRegistry:a:items -> dict[str, Command] {
    return |> <s>.registry.items;
}


:o:CommandShell:a:init (cmd_reg: CommandRegistry) {
    <s>.cmd_reg = cmd_reg;
    <s> |> cmd.Cmd.__init__;
}

:o:CommandShell:a:do_exit(arg: list) -> bool {
    return True;
}

:o:CommandShell:a:default(line: str) {
    try {
        args = |> line.split |> <s>.cmd_reg.parser.parse_args |> vars;
        command = args["command"] |> <s>.cmd_reg.get;
        if command {
            args.pop("command");
            ret = **args |> command.call;
            if ret {
                ret |> print;
            }
        }
    }
    except Exception as e {
        e |> print;
    }
}

:a:start_cli {
    parser = cmd_registry.parser;
    args = |> parser.parse_args;
    command = args.command |> cmd_registry.get;
    if command {
        args = args |> vars;
        "command" |> args.pop;
        ret = **args |> command.call;
        if ret {
            ret |> print;
        }
    }
    else {
        shell = |> CommandShell(cmd_registry).cmdloop;
    }
}
