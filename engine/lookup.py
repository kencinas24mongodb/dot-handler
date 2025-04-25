import re
from datetime import datetime
from pathlib import Path
from typing import Any

from typer import echo

from engine import storage
from engine.utils import DDLObjectTypeSupported


class DDLObjectTypeRegexBuilder:
    @staticmethod
    def views(name: str) -> re.Pattern:
        parts = name.split(".", 1)

        if len(parts) == 2 and "." in parts[1]:
            raise ValueError(f"This view name is invalid: {name}")

        if len(parts) == 1:
            return re.compile(r"\s+" + re.escape(name) + r"(?:\s+|($)?)", re.IGNORECASE | re.VERBOSE)
        else:
            return re.compile(r"\s+((?:" + re.escape(parts[0]) + r"\.)?" + re.escape(parts[1]) + r")(?:\s+|($)?)",
                              re.IGNORECASE | re.VERBOSE)


def lookup_dot_usages_from_file(dots: DDLObjectTypeSupported, do_name: str, ds_name: str, src_file: Path):
    # Check if the given dataset name exists!
    if not storage.exists(ds_name):
        raise FileNotFoundError(f"Given dataset name is not valid, does not exist: {ds_name}")
    else:
        ds = storage.load_dataset(ds_name)

    if do_name != "*":
        # DDL Object name is the one given by parameter
        table = [do_name]
    else:
        # Loads the given DDL Object Type definition table from the dataset, then use the keys
        table = list(ds.get('definitions', {}).get(dots.value, {}).keys())
        if len(table) == 0:
            echo("[WARNING] ⚠️ DDL Type object definition table is empty, please first run: `app find <dots> <input path>`")
            exit(1)

    with open(src_file, "r") as fp:
        data = fp.read()

    usage_records = {}
    for name in table:
        echo(f"[INFO] 🔍 Looking up usages of {dots.value} '{name}' in {src_file.absolute()}")

        # Check only DDL object names (views, but can be extended to any other)
        regex = getattr(DDLObjectTypeRegexBuilder, dots.value)
        if not regex:
            raise ValueError(f"Unsupported DOTS for Regex Builder: {dots.value}")

        regex = regex(name)
        for matching in regex.finditer(data):
            entry = {"filepath": str(src_file.absolute()), "line": data.count('\n', 0, matching.start()) + 1,
                     "timestamp": datetime.now().timestamp()}
            echo(f"[INFO] ✅ New usage entry found at line: {entry['line']}")
            if name not in usage_records:
                usage_records[name] = [entry]
            else:
                usage_records[name].append(entry)
        else:
            echo(f"[INFO] {'-' * 80}")
    return usage_records


def store_dot_usages(ds_name: str, dots: DDLObjectTypeSupported, records: dict[str, dict[str, Any]]):
    ds = storage.load_dataset(ds_name)

    collection = ds.get('usages', {})

    generation = collection.get('generation', 0) + 1

    table = collection.get(dots.value, {})

    # Create and formalize the usage table
    usage_table = {}
    for filepath, dot_tables in records.items():
        for dot_name, usages in dot_tables.items():
            if dot_name not in usage_table:
                usage_table[dot_name] = []
            usage_table[dot_name] += [{**usage, "generation": generation} for usage in usages]

    table.update(usage_table)
    collection[dots.value] = table
    collection['generation'] = generation
    ds['usages'] = collection


    storage.save_dataset(ds, ds_name)
    echo(f"[INFO] 💾 New lookup result was stored with generation {generation}")
