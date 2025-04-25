import re
from datetime import datetime
from pathlib import Path
from typing import List

from typer import echo

from engine import storage
from engine.configuration import ConfPolicy
from engine.configuration import get_config
from engine.utils import DDLDefinitionRecord, DDLObjectTypeSupported


class DDLNameFinderRE:
    VIEWS = re.compile(
        r"CREATE(?:\s+OR\s+REPLACE)?(?:\s+(?:FORCE|NOFORCE))?\s+VIEW\s+(?P<name>(?:[a-zA-Z_][\w$#]*\.)?[a-zA-Z_][\w$#]*)",
        re.IGNORECASE | re.VERBOSE)


class DDLObjectTypeFinder:
    @staticmethod
    def views(filepath: str, data: str):
        records = {}

        for matching in DDLNameFinderRE.VIEWS.finditer(data):
            record = DDLDefinitionRecord.from_definition(matching.group("name"), filepath,
                                                         data.count('\n', 0, matching.start()) + 1)

            if record.fullname in records:
                echo(f"[WARNING] ⚠️ The view '{record.fullname}' declaration is duplicated at line {record.line}")
            else:
                echo(f"[INFO] ✅ A new view was found at line {record.line}: '{record.fullname}'")
                records[record.fullname] = record

        return records


def find_dot_definition_from_file(dots: DDLObjectTypeSupported, src_filepaths: List[Path]):
    find_object_func = getattr(DDLObjectTypeFinder, dots.value)
    if not find_object_func:
        raise ValueError(f"Unsupported DOTS for Finder: {dots.value}")

    dot_table = {}

    for src_file in src_filepaths:
        echo(f"[INFO] 🔍 Searching definitions of {dots.value} in {src_file.absolute()}")

        # Make sure to clean the data input
        with open(src_file, "r") as fp:
            data = "\n".join([line.strip().lower() for line in fp.readlines()])

        dot_objects = find_object_func(f"{src_file.absolute()}", data)
        for key in dot_objects.keys():
            if key in dot_table:
                echo("[WARNING] ⚠️ Found a collision for DDL object definition: ")
                echo(f"\t📄 ORIGINAL:  {dot_table[key]}")
                echo(f"\t📄 COLLISION: {dot_objects[key]}")

                # Check collision policy
                policy = get_config("policy.collision")
                match policy:
                    case ConfPolicy.Collision.FAILURE.value:
                        echo(
                            "[ERROR] ❌ Collision Policy is set to FAILURE, to change it please use: `app config set 'policy.collision' [keep-original | override]`")
                        exit(1)
                    case ConfPolicy.Collision.KEEP_ORIGINAL.value:
                        echo(
                            "[INFO] 💬 Collision Policy is set to KEEP-ORIGINAL, to change it please use: `app config set 'policy.collision' [failure | override]`")
                        continue  # Skip this collision
                    case ConfPolicy.Collision.OVERRIDE.value:
                        echo(
                            "[INFO] 💬 Collision Policy is set to OVERRIDE, to change it please use: `app config set 'policy.collision' [keep-original | failure]`")

            dot_table[key] = dot_objects[key]

        echo(f"[INFO] {'-' * 80}")

    return dot_table


def store_dot_definitions(ds_name: str, dots: DDLObjectTypeSupported, dot_table: dict[str, DDLDefinitionRecord]):
    ds = storage.load_dataset(ds_name)

    collection = ds.get('definitions', {})

    table = collection.get(dots.value, {})

    for key, entry in dot_table.items():
        entry = entry.__dict__
        entry['timestamp'] = datetime.now().timestamp()

        table[key] = entry

    collection[dots.value] = table
    ds['definitions'] = collection
    storage.save_dataset(ds, ds_name)
