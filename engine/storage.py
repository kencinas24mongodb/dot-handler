import json
from datetime import datetime
from typing import Any

import typer

from engine.configuration import STORAGE_MAIN_DIR
from engine.utils import DDLDefinitionRecord


def rm(ds_name: str):
    ds_filepath = STORAGE_MAIN_DIR / "dataset" / f"{ds_name}.json"
    ds_filepath.unlink(missing_ok=True)


def exists(ds_name: str) -> bool:
    ds_filepath = STORAGE_MAIN_DIR / "dataset" / f"{ds_name}.json"
    return ds_filepath.exists()


def load_dataset(dataset_name: str) -> dict[str, Any]:
    ds_filepath = STORAGE_MAIN_DIR / "dataset" / f"{dataset_name}.json"
    ds_filepath.parent.mkdir(parents=True, exist_ok=True)  # Make sure the "dataset" folder exists

    if not ds_filepath.exists():
        return {}
    else:
        with open(ds_filepath, "r") as fp:
            return json.load(fp)


def save_dataset(dataset: dict[str, Any], dataset_name: str):
    ds_filepath = STORAGE_MAIN_DIR / "dataset" / f"{dataset_name}.json"
    ds_filepath.parent.mkdir(parents=True, exist_ok=True)  # Make sure the "dataset" folder exists

    with open(ds_filepath, "w") as fp:
        json.dump(dataset, fp)


def store(dataset_name: str, collection_name: str, ddl_object_type: str, objects: dict[str, DDLDefinitionRecord]):
    ds = load_dataset(dataset_name)

    collection = ds.get(collection_name, {})

    table = collection.get(ddl_object_type, {})

    for key, entry in objects.items():
        typer.echo(f"{key}: {entry}")
        entry = entry.__dict__
        entry['timestamp'] = datetime.now().timestamp()

        table[key] = entry

    collection[ddl_object_type] = table
    ds[collection_name] = collection

    save_dataset(ds, dataset_name)
