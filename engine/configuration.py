import json
import os
from enum import Enum
from pathlib import Path
from typing import Any
from typer import echo

# Set up the main storage directory
STORAGE_MAIN_DIR = Path(os.path.expanduser("~")) / ".mdb_tools" / "dot-handler"
STORAGE_MAIN_DIR.mkdir(parents=True, exist_ok=True)


class ConfCommand(str, Enum):
    SET = "set"
    GET = "get"
    LIST = "list"
    CLEAR = "clear"

class ConfPolicy:
    class Collision(str, Enum):
        OVERRIDE = "override"
        KEEP_ORIGINAL = "keep-original"
        FAILURE = "failure"




def load_conf() -> dict[str, Any]:
    conf_file = STORAGE_MAIN_DIR / ".conf"
    if not conf_file.exists():
        # Default configuration
        conf = {"db.schema": "user", "policy.collision": ConfPolicy.Collision.FAILURE}
    else:
        with open(conf_file, "r") as fp:
            conf = json.load(fp)
    return conf


def save_conf(conf: dict[str, Any]):
    conf_file = STORAGE_MAIN_DIR / ".conf"
    with open(conf_file, "w") as fp:
        json.dump(conf, fp)


def get_config(key: str, default: str | None = None) -> str | None:
    conf = load_conf()
    return conf.get(key, default)


def set_config(key: str, value: Any | None):
    conf = load_conf()
    if value is None and key in conf:
        del conf[key]
        echo(f"[INFO] 🗑️ {key} was deleted!")
    elif value is not None:
        conf[key] = value
    else:
        return
    save_conf(conf)
