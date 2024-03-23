import json
import sys
import yaml
from operations.local.logging import baton_log


def read_json(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)


def read_yaml(file_path: str):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def save_yaml(object: object, file_path: str, sort_keys=True):
    with open(file_path, "w") as f:
        yaml.dump(object, f, sort_keys=sort_keys)


def load_config(path=None):
    path = path if path else sys.argv[1]
    baton_log.info(f"Loading config from {path}")
    return read_yaml(path)
