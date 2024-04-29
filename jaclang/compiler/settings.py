import argparse
import configparser
import os

class Settings:
    def __init__(self):
        self.config={}
        self.load_config_file()
        # self.load_environment_variables()
        # self.load_command_line_arguments()

    def load_config_file(self):
        currrent_path = os.path.dirname(__file__)
        config_path = os.path.join(currrent_path, 'config.ini')
        configs = configparser.ConfigParser()
        # configs.read(config_path)
        # print(configs['JAC_OS_ENV_VAR']["JAC_PROC_DEBUG"])
        if os.path.exists(config_path):
            configs.read(config_path)
            self.config.update({key: self.convert_type(value) for key, value in configs['JAC_OS_ENV_VAR'].items()})
        else:
            print("Warning: Config file not found, using default settings.")

    def load_environment_variables(self): 
        env_vars = ['HOST', 'PORT', 'DEBUG']
        for var in env_vars:
            if var in os.environ:
                self.config[var.lower()] = self.convert_type(os.environ[var])

    def load_command_line_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', type=str)
        parser.add_argument('--port', type=int)
        parser.add_argument('--debug', action='store_true')
        args = parser.parse_args()
        # Update only if argument is provided
        for key, value in vars(args).items():
            if value is not None:
                self.config[key] = value

    def convert_type(self, value):
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit():
            return int(value)
        return value

    def __getitem__(self, item):
        return self.config.get(item, None)

    def __repr__(self):
        return f"Settings({self.config})"