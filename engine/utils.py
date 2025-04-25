from enum import Enum
from typer import echo

from engine.configuration import get_config


class DDLObjectTypeSupported(str, Enum):
    views = "views"

class DatasetOutput(str, Enum):
    STDOUT = "stdout"
    FILE = "file"

class DDLDefinitionRecord(object):
    @classmethod
    def from_definition(cls, definition: str, filepath: str, line: int) -> 'DDLDefinitionRecord':
        parts = definition.split(".")
        if definition.startswith(".") or definition.endswith(".") or len(parts) > 2:
            echo(f"[ERROR] ❌ This definition is wrong, unable to get DDL object type name from: {definition}")
            exit(1)

        if len(parts) == 1:
            return cls(definition, get_config("db.schema"), filepath, line)
        else:
            return cls(parts[1], parts[0], filepath, line)

    def __init__(self, name: str, schema: str, filepath: str, line: int):
        self.name = name
        self.schema = schema
        self.filepath = filepath
        self.line = line

    @property
    def fullname(self) -> str:
        return f"{self.schema}.{self.name}"

    def __str__(self):
        return (f"DDLDefinitionRecord(name={self.name}, "
                f"schema={self.schema}, "
                f"filepath={self.filepath}, "
                f"line={self.line})")
