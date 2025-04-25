from pathlib import Path

import typer

DDL_OBJECT_TYPES_SUPPORTED = ["views", ]


def validate_ddl_object_type(ddl_object_type: str) -> str:
    """

    :param ddl_object_type:
    :return:
    """
    if ddl_object_type.strip().lower() not in DDL_OBJECT_TYPES_SUPPORTED:
        raise typer.BadParameter(f"'{ddl_object_type}' not supported: {DDL_OBJECT_TYPES_SUPPORTED}")
    return ddl_object_type


def validate_source_path(source_path: str) -> str:
    """

    :param source_path:
    :return:
    """
    path = Path(source_path)

    if not path.exists():
        raise typer.BadParameter(f"{source_path} does not exist!")

    if not path.is_dir():
        raise typer.BadParameter(f"{source_path} is not a directory!")

    return source_path
