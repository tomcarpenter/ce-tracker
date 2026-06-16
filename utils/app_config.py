"""
App-level configuration for paths needed before Storage can be initialized.
"""

from pathlib import Path
import json
from typing import Any

from utils.storage import Storage


APP_CONFIG_PATH = Path("app_config.json")
DEFAULT_DATA_DIR = "data"


def load_app_config() -> dict[str, Any]:
    defaults = {"data_dir": DEFAULT_DATA_DIR}

    if not APP_CONFIG_PATH.exists():
        return defaults

    try:
        with open(APP_CONFIG_PATH, "r") as f:
            loaded = json.load(f)
        defaults.update(loaded)
    except Exception:
        pass

    return defaults


def save_app_config(config: dict[str, Any]) -> None:
    with open(APP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def configured_data_dir() -> str:
    return load_app_config().get("data_dir") or DEFAULT_DATA_DIR


def configured_storage() -> Storage:
    return Storage(data_dir=configured_data_dir())
