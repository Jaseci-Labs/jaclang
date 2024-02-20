# # main_cli_app.py
# import argparse
# import pluggy
# from cli_plugin_spec import CLISpec

# # Create a plugin manager and load plugins
# plugin_manager = pluggy.PluginManager("cli")
# plugin_manager.add_hookspecs(CLISpec)
# plugin_manager.load_setuptools_entrypoints("cli")

# # Set up the main parser
# parser = argparse.ArgumentParser(description="Plugin-extendable CLI")
# subparsers = parser.add_subparsers(help='commands')

# # Let plugins add their commands
# plugin_manager.hook.add_command(parser=subparsers)

# # Parse arguments and execute
# args = parser.parse_args()
# if hasattr(args, 'func'):
#     args.func(args)
# else:
#     parser.print_help()
