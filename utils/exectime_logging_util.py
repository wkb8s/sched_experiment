import os
import logging

def create_directory(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.debug(f"Directory created: {directory}")
    else:
        logging.debug(f"Directory already exists: {directory}")

def delete_file(file_path: str) -> None:
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            logging.info(f"File '{file_path}' deleted successfully.")
        else:
            logging.info(f"File '{file_path}' not found.")
    except PermissionError:
        raise PermissionError(f"Permission denied: Unable to delete '{file_path}'.")
    except OSError as e:
        raise OSError(f"Error deleting file '{file_path}': {e}")

import yaml

def get_config(key: str) -> str:
    try:
        config_path = "./config.yaml"
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            log_string = config.get(key, '')
            if not isinstance(log_string, str):
                raise ValueError(f"Expected {key} to be a string, but got {type(log_string).__name__}")
            return log_string
    except FileNotFoundError:
        print(f"The file {config_path} was not found.")
        return ''
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return ''
    except ValueError as ve:
        print(ve)
        return ''

